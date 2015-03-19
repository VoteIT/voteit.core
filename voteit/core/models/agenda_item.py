from arche.security import get_acl_registry
from pyramid.httpexceptions import HTTPForbidden
from pyramid.security import Deny
from pyramid.security import Everyone
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface
from repoze.folder.interfaces import IObjectAddedEvent
from zope.interface import implementer

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IProposal
from voteit.core.models.workflow_aware import WorkflowAware


@implementer(IAgendaItem, ICatalogMetadataEnabled)
class AgendaItem(BaseContent, WorkflowAware):
    """ Agenda Item content type.
        See :mod:`voteit.core.models.interfaces.IAgendaItem`.
        All methods are documented in the interface of this class.
    """
    type_name = 'AgendaItem'
    type_title = _("Agenda item")
    add_permission = security.ADD_AGENDA_ITEM
    custom_mutators = {'proposal_block': '_set_proposal_block', 'discussion_block': '_set_discussion_block'}

    @property
    def __acl__(self):
        acl = get_acl_registry()
        state = self.get_workflow_state()
        if state == 'closed':
            #Check if the meeting is closed, if not discussion should be allowed +
            #it should be allowed to change the workflow back
            if self.__parent__.get_workflow_state() == 'closed':
                return acl.get_acl('AgendaItem:closed_meeting')
            return acl.get_acl('AgendaItem:closed_ai')
        if state == 'private':
            return acl.get_acl('AgendaItem:private')
        perms = []
        if self.get_field_value('proposal_block', False) == True:
            perms.append((Deny, Everyone, security.ADD_PROPOSAL))
        if self.get_field_value('discussion_block', False) == True:
            perms.append((Deny, Everyone, security.ADD_DISCUSSION_POST))
        perms.extend(self.__parent__.__acl__)
        return perms

    @property
    def proposal_block(self): #Arche compat
        return self.get_field_value('proposal_block', False)
    @proposal_block.setter
    def proposal_block(self, value):
        self._set_proposal_block(value)

    @property
    def discussion_block(self): #Arche compat
        return self.get_field_value('discussion_block', False)
    @discussion_block.setter
    def discussion_block(self, value):
        self._set_discussion_block(value)

    def _set_proposal_block(self, value, key=None):
        isinstance(value, bool)
        self.field_storage['proposal_block'] = value

    def _set_discussion_block(self, value, key=None):
        isinstance(value, bool)
        self.field_storage['discussion_block'] = value

    @property
    def start_time(self):
        """ Set by a subscriber when this item is opened. """
        return self.get_field_value('start_time')

    @property
    def end_time(self):
        """ Set by a subscriber when this item closes. """
        return self.get_field_value('end_time')


def closing_agenda_item_callback(context, info):
    """ Callback for workflow action. When an agenda item is closed,
        all contained proposals that haven't been handled should be set to
        "unhandled".
        If there are any open polls, this should raise an exception or an error message of some sort.
    """
    request = get_current_request() #Should be okay to use here since this method is called very seldom.
    #get_content returns a generator. It's "True" even if it's empty!
    if tuple(context.get_content(iface=IPoll, states='ongoing')):
        err_msg = _(u"error_polls_not_closed_cant_close_ai",
                    default = u"You can't close an agenda item that has ongoing polls in it. Close the polls first!")
        raise HTTPForbidden(err_msg)
    for proposal in context.get_content(iface=IProposal, states='published'):
        proposal.set_workflow_state(request, 'unhandled')

def ongoing_agenda_item_callback(context, info):
    """ Callback for workflow action. An agenda item can't be set as ongoing when meeting is not ongoing
    """
    meeting = find_interface(context, IMeeting)
    if meeting and meeting.get_workflow_state() != 'ongoing':
        err_msg = _(u"error_ai_cannot_be_ongoing_in_not_ongoing_meeting",
                    default = u"You can't set an agenda item to ongoing if the meeting is not ongoing.")
        raise HTTPForbidden(err_msg)

def set_initial_order(obj, event):
    """ Subscriber to set the initial order of the agenda item """
    meeting = find_interface(obj, IMeeting)
    assert meeting
    order = 0
    for ai in meeting.values():
        if IAgendaItem.providedBy(ai):
            if ai.get_field_value('order') >= order:
                order = ai.get_field_value('order')+1

    obj.set_field_appstruct({'order': order})


def includeme(config):
    config.add_content_factory(AgendaItem, addable_to = 'Meeting')
    config.add_subscriber(set_initial_order, [IAgendaItem, IObjectAddedEvent])
    _PRIV_MOD_PERMS = (security.VIEW,
                       security.EDIT,
                       security.DELETE,
                       security.MODERATE_MEETING,
                       security.CHANGE_WORKFLOW_STATE, )
    _CLOSED_AI_MOD_PERMS = (security.VIEW,
                            security.CHANGE_WORKFLOW_STATE,
                            security.ADD_DISCUSSION_POST,
                            security.MODERATE_MEETING, )
    aclreg = config.registry.acl
    private = aclreg.new_acl('AgendaItem:private')
    private.add(security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS)
    private.add(security.ROLE_ADMIN, _PRIV_MOD_PERMS)
    private.add(security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS)
    private.add(security.ROLE_MODERATOR, _PRIV_MOD_PERMS)
    closed_ai = aclreg.new_acl('AgendaItem:closed_ai')
    closed_ai.add(security.ROLE_ADMIN, _CLOSED_AI_MOD_PERMS)
    closed_ai.add(security.ROLE_MODERATOR, _CLOSED_AI_MOD_PERMS)
    closed_ai.add(security.ROLE_DISCUSS, security.ADD_DISCUSSION_POST)
    closed_ai.add(security.ROLE_VIEWER, security.VIEW)
    closed_meeting = aclreg.new_acl('AgendaItem:closed_meeting')
    closed_meeting.add(security.ROLE_ADMIN, security.VIEW)
    closed_meeting.add(security.ROLE_MODERATOR, security.VIEW)
    closed_meeting.add(security.ROLE_VIEWER, security.VIEW)
