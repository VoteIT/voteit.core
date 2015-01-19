import string
from random import choice
from uuid import uuid4

from repoze.folder import Folder
from persistent.list import PersistentList
from zope.interface import implementer
from pyramid.traversal import find_interface
from pyramid.exceptions import Forbidden
from pyramid.security import authenticated_userid
from betahaus.pyracont.decorators import content_factory
from betahaus.viewcomponent import render_view_action

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IInviteTicket
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.models.date_time_util import utcnow
from voteit.core.helpers import send_email


SELECTABLE_ROLES = (security.ROLE_MODERATOR,
                    security.ROLE_DISCUSS,
                    security.ROLE_PROPOSE,
                    security.ROLE_VOTER,
                    security.ROLE_VIEWER,
                    )


#@content_factory('InviteTicket', title=_(u"Invite ticket"))
@implementer(IInviteTicket)
class InviteTicket(Folder, WorkflowAware):
    """ Invite ticket. Send these to give access to new users.
        See :mod:`voteit.core.models.interfaces.IInviteTicket`.
        All methods are documented in the interface of this class.
    """
    type_name = 'InviteTicket'
#    allowed_contexts = () #Not addable through regular forms
#    add_permission = None
    #No schemas
    
    def __init__(self, email, roles, message = u"", sent_by = None):
        self.email = email.lower()
        for role in roles:
            if role not in SELECTABLE_ROLES:
                raise ValueError("InviteTicket got '%s' as a role, and that isn't selectable." % role)
        self.roles = roles
        assert isinstance(message, basestring)
        self.message = message
        self.created = utcnow()
        self.closed = None
        self.claimed_by = None
        self.sent_by = sent_by
        self.token = ''.join([choice(string.letters + string.digits) for x in range(30)])
        self.sent_dates = PersistentList()
        self.uid = unicode(uuid4())
        super(InviteTicket, self).__init__()

    def send(self, request, message = u""):
        if self.closed: #Just as a precaution
            return
        meeting = find_interface(self, IMeeting)
        html = render_view_action(self, request, 'email', 'invite_ticket', message = message)
        subject = _(u"Invitation to ${meeting_title}", mapping = {'meeting_title': meeting.title})
        if send_email(subject = subject, recipients = self.email, html = html, request = request, send_immediately = True):
            self.sent_dates.append(utcnow())

    def claim(self, request):
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


def includeme(config):
    config.add_content_factory(InviteTicket)
