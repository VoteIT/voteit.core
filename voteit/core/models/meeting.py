from BTrees.OOBTree import OOBTree
from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.security import DENY_ALL
from betahaus.pyracont.decorators import content_factory
from pyramid.httpexceptions import HTTPForbidden

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.workflow_aware import WorkflowAware


_MODERATOR_DEFAULTS = (security.VIEW,
                       security.EDIT,
                       security.MANAGE_GROUPS,
                       security.MODERATE_MEETING,
                       security.DELETE,
                       security.CHANGE_WORKFLOW_STATE, )

ACL = {}
ACL['default'] = [(Allow, security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_ADMIN, _MODERATOR_DEFAULTS),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, _MODERATOR_DEFAULTS),
                  #(Allow, security.ROLE_OWNER, (security.VIEW, security.EDIT, )),
                  (Allow, security.ROLE_DISCUSS, (security.ADD_DISCUSSION_POST, )),
                  (Allow, security.ROLE_PROPOSE, (security.ADD_PROPOSAL, )),
                  (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                  (Allow, Authenticated, security.REQUEST_MEETING_ACCESS),
                  DENY_ALL,
                   ]
ACL['private'] = [(Allow, security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_ADMIN, _MODERATOR_DEFAULTS),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, _MODERATOR_DEFAULTS),
                  DENY_ALL,
                ]
ACL['closed'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.MANAGE_GROUPS, security.DELETE, )),
                 (Allow, security.ROLE_MODERATOR, (security.VIEW, security.MANAGE_GROUPS, )),
                 (Allow, security.ROLE_VIEWER, (security.VIEW, )),
                 DENY_ALL,
                ]


@content_factory('Meeting', title=_(u"Meeting"))
class Meeting(BaseContent, WorkflowAware):
    """ Meeting content. """
    implements(IMeeting, ICatalogMetadataEnabled)
    content_type = 'Meeting'
    display_name = _(u"Meeting")
    allowed_contexts = ('SiteRoot',)
    add_permission = security.ADD_MEETING
    #FIXME: Property schema should return different add schema when user is not an admin.
    #Ie captcha
    schemas = {'add': 'MeetingSchema', 'edit': 'MeetingSchema'}

    @property
    def __acl__(self):
        return ACL.get(self.get_workflow_state(), ACL['default'])

    @property
    def start_time(self):
        """ Returns start time of the earliest visible agenda item
            that has a start time set. Could return None if no time exists.
        """
        for ai in self.get_content(iface=IAgendaItem, sort_on='start_time'):
            if ai.get_workflow_state() == 'private':
                continue
            if ai.start_time is not None:
                return ai.start_time

    @property
    def end_time(self):
        return self.get_field_value('end_time')

    @property
    def invite_tickets(self):
        """ Storage for InviteTickets. Works pretty much like a folder. """
        storage = getattr(self, '__invite_tickets__', None)
        if storage is None:
            storage = self.__invite_tickets__ =  OOBTree()
        return storage

    def add_invite_ticket(self, ticket, request):
        """ Add an invite ticket to the storage invite_tickets.
            It will also set the __parent__ attribute to allow
            lookup of objects. The parent of the ticket will
            in that case be the meeting.
        """
        ticket.__parent__ = self
        self.invite_tickets[ticket.email] = ticket
        ticket.send(request)


def closing_meeting_callback(context, info):
    """ Callback for workflow action. When a meeting is closed,
        raise an exception if any agenda item is ongoing.
    """
    #get_content returns a generator. It's "True" even if it's empty!
    if tuple(context.get_content(iface=IAgendaItem, states='ongoing')):
        err_msg = _(u"error_cant_close_meeting_with_ongoing_ais",
                    default = u"This meeting still has ongoing Agenda items in it. You can't close it until they're closed.")
        raise HTTPForbidden(err_msg)

