from BTrees.OOBTree import OOBTree
from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.traversal import find_root
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
                  (Allow, security.ROLE_ADMIN, security.MANAGE_SERVER),
                  (Allow, security.ROLE_ADMIN, _MODERATOR_DEFAULTS),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, _MODERATOR_DEFAULTS),
                  (Allow, security.ROLE_DISCUSS, (security.ADD_DISCUSSION_POST, )),
                  (Allow, security.ROLE_PROPOSE, (security.ADD_PROPOSAL, )),
                  (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                  DENY_ALL,
                   ]

ACL['closed'] = [(Allow, security.ROLE_ADMIN, (security.VIEW, security.MODERATE_MEETING, security.MANAGE_GROUPS, security.DELETE, security.CHANGE_WORKFLOW_STATE)),
                 (Allow, security.ROLE_MODERATOR, (security.VIEW, security.MODERATE_MEETING, security.MANAGE_GROUPS, )),
                 (Allow, security.ROLE_VIEWER, (security.VIEW, )),
                 DENY_ALL,
                ]


@content_factory('Meeting', title=_(u"Meeting"))
class Meeting(BaseContent, WorkflowAware):
    """ Meeting content type.
        See :mod:`voteit.core.models.interfaces.IMeeting`.
        All methods are documented in the interface of this class.
    """
    implements(IMeeting, ICatalogMetadataEnabled)
    content_type = 'Meeting'
    display_name = _(u"Meeting")
    allowed_contexts = ('SiteRoot',)
    add_permission = security.ADD_MEETING
    #FIXME: Property schema should return different add schema when user is not an admin.
    #Ie captcha
    schemas = {'add': 'AddMeetingSchema', 'edit': 'EditMeetingSchema'}
    custom_mutators = {'copy_perms_and_users': 'copy_perms_and_users'}

    def __init__(self, data=None, **kwargs):
        """ When meetings are added, whoever added them should become moderator and voter.
            BaseContent will have added userid to creators attribute.
        """
        super(Meeting, self).__init__(data=data, **kwargs)
        if len(self.creators) and self.creators[0]:
            userid = self.creators[0]
            #We can't send the event here since the object isn't attached to the resource tree yet
            #When it is attached, an event will be sent.
            self.add_groups(userid, (security.ROLE_MODERATOR, security.ROLE_VOTER, ), event = False)

    @property
    def __acl__(self):
        return ACL.get(self.get_workflow_state(), ACL['default'])

    @property
    def start_time(self):
        return self.get_field_value('start_time')

    @property
    def end_time(self):
        return self.get_field_value('end_time')

    @property
    def invite_tickets(self):
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

    def copy_users_and_perms(self, name, event = True):
        root = find_root(self)
        origin = root[name]
        value = origin.get_security()
        self.set_security(value, event = event)


def closing_meeting_callback(context, info):
    """ Callback for workflow action. When a meeting is closed,
        raise an exception if any agenda item is ongoing.
    """
    #get_content returns a generator. It's "True" even if it's empty!
    if tuple(context.get_content(iface=IAgendaItem, states=('ongoing', 'upcoming'))):
        err_msg = _(u"error_cant_close_meeting_with_ongoing_ais",
                    default = u"This meeting still has ongoing or upcoming Agenda items in it. You can't close it until they're closed.")
        raise HTTPForbidden(err_msg)

