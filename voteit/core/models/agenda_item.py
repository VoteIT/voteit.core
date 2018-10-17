from arche.interfaces import IWorkflowBeforeTransition
from arche.resources import ContextACLMixin
from arche.security import get_acl_registry
from pyramid.httpexceptions import HTTPForbidden
from pyramid.security import Deny
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from repoze.catalog.query import Eq
from zope.interface import implementer

from voteit.core import _
from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.workflow_aware import WorkflowCompatMixin


@implementer(IAgendaItem)
class AgendaItem(BaseContent, ContextACLMixin, WorkflowCompatMixin):
    """ Agenda Item content type.
        See :mod:`voteit.core.models.interfaces.IAgendaItem`.
        All methods are documented in the interface of this class.
    """
    type_name = 'AgendaItem'
    type_title = _("Agenda item")
    add_permission = security.ADD_AGENDA_ITEM
    # FIXME: Remove and migrate this
    custom_mutators = {'proposal_block': '_set_proposal_block', 'discussion_block': '_set_discussion_block'}
    css_icon = 'glyphicon glyphicon-list-alt'
    collapsible_limit = None

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
            perms.append((Deny, security.ROLE_PROPOSE, security.ADD_PROPOSAL))
        if self.get_field_value('discussion_block', False) == True:
            perms.append((Deny, security.ROLE_DISCUSS, security.ADD_DISCUSSION_POST))
        perms.extend(self.__parent__.__acl__)
        return perms

    @property
    def body(self): #Arche compat
        return self.get_field_value('body', "")
    @body.setter
    def body(self, value):
        self.set_field_value('body', value)

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
    @start_time.setter
    def start_time(self, value):
        self.set_field_value('start_time', value)

    @property
    def end_time(self):
        """ Set by a subscriber when this item closes. """
        return self.get_field_value('end_time')
    @end_time.setter
    def end_time(self, value):
        self.set_field_value('end_time', value)

    @property
    def hashtag(self):
        return self.get_field_value('hashtag', '')
    @hashtag.setter
    def hashtag(self, value):
        self.set_field_value('hashtag', value)

    @property
    def tags(self):
        return self.get_field_value('tags', frozenset())
    @tags.setter
    def tags(self, value):
        self.set_field_value('tags', frozenset(value))


def check_no_open_polls(ai, event):
    """ Make sure no polls are ongoing if we close agenda item. """
    if event.to_state == 'closed':
        root = find_root(ai)
        query = Eq('type_name', 'Poll') & Eq('wf_state', 'ongoing')
        res = root.catalog.query(query)[0]
        if res.total:
            err_msg = _(u"error_polls_not_closed_cant_close_ai",
                        default=u"You can't close an agenda item that has ongoing polls in it. Close the polls first!")
            raise HTTPForbidden(err_msg)


def check_meeting_ongoing(ai, event):
    meeting = find_interface(ai, IMeeting)
    if meeting:
        if event.to_state == 'ongoing' and meeting.wf_state != 'ongoing':
            err_msg = _(u"error_ai_cannot_be_ongoing_in_not_ongoing_meeting",
                        default = u"You can't set an agenda item to ongoing if the meeting is not ongoing.")
            raise HTTPForbidden(err_msg)



def includeme(config):
    config.add_content_factory(AgendaItem, addable_to = 'Meeting')
    config.add_subscriber(check_no_open_polls, [IAgendaItem, IWorkflowBeforeTransition])
    config.add_subscriber(check_meeting_ongoing, [IAgendaItem, IWorkflowBeforeTransition])
