import string
from random import choice
from uuid import uuid4

from repoze.folder import Folder
from zope.component import getUtility
from zope.interface import implements
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.traversal import find_interface
from pyramid.url import resource_url
from pyramid.exceptions import Forbidden
from pyramid.security import authenticated_userid
from pyramid.renderers import render
from betahaus.pyracont.decorators import content_factory

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IInviteTicket
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.models.date_time_util import utcnow


SELECTABLE_ROLES = (security.ROLE_MODERATOR,
                    security.ROLE_DISCUSS,
                    security.ROLE_PROPOSE,
                    security.ROLE_VOTER,
                    security.ROLE_VIEWER,
                    )


@content_factory('InviteTicket', title=_(u"Invite ticket"))
class InviteTicket(Folder, WorkflowAware):
    """ Invite ticket. Send these to give access to new users.
        See IInviteTicket for more info.
    """
    implements(IInviteTicket)
    content_type = 'InviteTicket'
    allowed_contexts = () #Not addable through regular forms
    add_permission = None
    #No schemas
    
    def __init__(self, email, roles, message):
        self.email = email
        for role in roles:
            if role not in SELECTABLE_ROLES:
                raise ValueError("InviteTicket got '%s' as a role, and that isn't selectable." % role)
        self.roles = roles
        self.message = message
        self.created = utcnow()
        self.closed = None
        self.claimed_by = None
        self.token = ''.join([choice(string.letters + string.digits) for x in range(30)])
        self.sent_dates = []
        self.uid = unicode(uuid4())
        super(InviteTicket, self).__init__()

    def send(self, request):
        """ Send message about invite ticket. """
        response = {}

        meeting = find_interface(self, IMeeting)
        assert meeting
        
        form_url = "%sticket" % resource_url(meeting, request)
        response['access_link'] = form_url + '?email=%s&token=%s' % (self.email, self.token)
        response['message'] = self.message
        
        sender = "%s <%s>" % (meeting.get_field_value('meeting_mail_name'), meeting.get_field_value('meeting_mail_address'))
        body_html = render('../views/templates/invite_ticket_email.pt', response, request=request)

        msg = Message(subject=_(u"VoteIT meeting invitation"),
                      sender = sender and sender or None,
                      recipients=[self.email],
                      html=body_html)

        mailer = get_mailer(request)
        mailer.send(msg)

        self.sent_dates.append(utcnow())

    def claim(self, request):
        """ Handle claim of this ticket. Set permissions for meeting and set the ticket as closed. """
        #Is the ticket open?
        if self.get_workflow_state() != 'open':
            raise Forbidden("Access already granted with this ticket")
        #Find required resources and do some basic validation
        meeting = find_interface(self, IMeeting)
        assert meeting
        
        userid = authenticated_userid(request)
        if userid is None:
            raise Forbidden("You can't claim a ticket unless you're authenticated.")
        
        meeting.add_groups(userid, self.roles)
        self.claimed_by = userid

        self.set_workflow_state(request, 'closed')
        
        self.closed = utcnow()
