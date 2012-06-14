from zope.interface import implements
from pyramid.traversal import find_interface
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.threadlocal import get_current_request
from betahaus.pyracont.decorators import content_factory
from pyramid.httpexceptions import HTTPForbidden

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import ICatalogMetadataEnabled


_PRIV_MOD_PERMS = (security.VIEW,
                   security.EDIT,
                   security.DELETE,
                   security.MODERATE_MEETING,
                   security.CHANGE_WORKFLOW_STATE, )

_CLOSED_AI_MOD_PERMS = (security.VIEW,
                        security.CHANGE_WORKFLOW_STATE,
                        security.ADD_DISCUSSION_POST,
                        security.MODERATE_MEETING, )


ACL = {}
ACL['private'] = [(Allow, security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_ADMIN, _PRIV_MOD_PERMS),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, _PRIV_MOD_PERMS),
                  DENY_ALL,
                ]
ACL['closed_ai'] = [(Allow, security.ROLE_ADMIN, _CLOSED_AI_MOD_PERMS),
                    (Allow, security.ROLE_MODERATOR, _CLOSED_AI_MOD_PERMS),
                    (Allow, security.ROLE_DISCUSS, (security.ADD_DISCUSSION_POST, )),
                    (Allow, security.ROLE_VIEWER, (security.VIEW, )),
                    DENY_ALL,
                   ]
ACL['closed_meeting'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, )),
                         (Allow, security.ROLE_MODERATOR, (security.VIEW, )),
                         (Allow, security.ROLE_VIEWER, (security.VIEW, )),
                         DENY_ALL,
                        ]


@content_factory('AgendaItem', title=_(u"Agenda item"))
class AgendaItem(BaseContent, WorkflowAware):
    """ Agenda Item content type.
        See :mod:`voteit.core.models.interfaces.IAgendaItem`.
        All methods are documented in the interface of this class.
    """
    implements(IAgendaItem, ICatalogMetadataEnabled)
    content_type = 'AgendaItem'
    display_name = _(u"Agenda item")
    allowed_contexts = ('Meeting',)
    add_permission = security.ADD_AGENDA_ITEM
    schemas = {'edit': 'EditAgendaItemSchema', 'add': 'AddAgendaItemSchema'}

    @property
    def __acl__(self):
        state = self.get_workflow_state()
        if state == 'closed':
            #Check if the meeting is closed, if not discussion should be allowed +
            #it should be allowed to change the workflow back
            if self.__parent__.get_workflow_state() == 'closed':
                return ACL['closed_meeting']
            return ACL['closed_ai']
        if state == 'private':
            return ACL['private']

        raise AttributeError("Go fetch parents acl")

    @property
    def start_time(self):
        return self.get_field_value('start_time')

    @property
    def end_time(self):
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
