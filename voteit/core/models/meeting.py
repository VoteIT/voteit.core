import colander
import deform
from BTrees.OOBTree import OOBTree
from zope.interface import implements
from pyramid.security import Allow, DENY_ALL, ALL_PERMISSIONS, Authenticated
from repoze.folder.interfaces import IObjectAddedEvent
from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.validators import html_string_validator
from voteit.core.models.log import Logs

_MODERATOR_DEFAULTS = (security.VIEW, security.EDIT, security.MANAGE_GROUPS,
                       security.MODERATE_MEETING, security.DELETE, security.CHANGE_WORKFLOW_STATE, )

ACL = {}
ACL['default'] = [(Allow, security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_ADMIN, _MODERATOR_DEFAULTS),
                  (Allow, security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS),
                  (Allow, security.ROLE_MODERATOR, _MODERATOR_DEFAULTS),
                  (Allow, security.ROLE_OWNER, (security.VIEW, security.EDIT, )),
                  (Allow, security.ROLE_PARTICIPANT, (security.VIEW, security.ADD_PROPOSAL, security.ADD_DISCUSSION_POST, )),
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
                 (Allow, security.ROLE_OWNER, (security.VIEW, )),
                 (Allow, security.ROLE_PARTICIPANT, (security.VIEW, )),
                 (Allow, security.ROLE_VIEWER, (security.VIEW, )),
                 DENY_ALL,
                ]


class Meeting(BaseContent, WorkflowAware):
    """ Meeting content. """
    implements(IMeeting, ICatalogMetadataEnabled)
    content_type = 'Meeting'
    display_name = _(u"Meeting")
    allowed_contexts = ('SiteRoot',)
    add_permission = security.ADD_MEETING

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


def construct_schema(**kwargs):
    if kwargs.get('type') == 'request_access':
        class RequestAccessSchema(colander.Schema):
            message = colander.SchemaNode(colander.String(),
                                          title = _(u"Message"),
                                          validator = colander.All(colander.Length(5, 999), html_string_validator,),
                                          default = _(u"Knock knock - Please let me access the meeting."),
                                          widget = deform.widget.TextAreaWidget(rows=5, cols=40),)
        return RequestAccessSchema()
    
    #Default schema
    class MeetingSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String())
        description = colander.SchemaNode(
            colander.String(),
            missing = u"",
            widget=deform.widget.TextAreaWidget(rows=10, cols=60))
        meeting_mail_name = colander.SchemaNode(colander.String(),
                                                title = _(u"Name visible on system mail sent from this meeting"),
                                                default = _(u"VoteIT"),)
        meeting_mail_address = colander.SchemaNode(colander.String(),
                                                title = _(u"Email address to send from"),
                                                default = _(u"noreply@somehost.voteit"),
                                                validator = colander.All(colander.Email(msg = _(u"Invalid email address")), html_string_validator,),)
    return MeetingSchema()

def includeme(config):
    from voteit.core.app import register_content_info
    register_content_info(construct_schema, Meeting, registry=config.registry)

def closing_meeting_callback(context, info):
    """ Callback for workflow action. When a meeting is closed,
        raise an exception if any agenda item is active.
    """
    #get_content returns a generator. It's "True" even if it's empty!
    if tuple(context.get_content(iface=IAgendaItem, state='active')):
        raise Exception("This meeting still has open Agenda items in it. You can't close it until they're closed.")

