import string
from random import choice
from uuid import uuid4

from arche.utils import send_email
from betahaus.viewcomponent import render_view_action
from persistent.list import PersistentList
from pyramid.exceptions import HTTPForbidden
from pyramid.traversal import find_interface
from repoze.folder import Folder
from zope.interface import implementer
from six import string_types

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IInviteTicket
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.models.date_time_util import utcnow


SELECTABLE_ROLES = (security.ROLE_MODERATOR,
                    security.ROLE_DISCUSS,
                    security.ROLE_PROPOSE,
                    security.ROLE_VOTER,
                    security.ROLE_VIEWER,
                    )


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

    @property
    def content_type(self):
        return self.type_name #b/c

    def __init__(self, email, roles, message = u"", sent_by = None):
        self.email = email.lower()
        for role in roles:
            if role not in SELECTABLE_ROLES:
                raise ValueError("InviteTicket got '%s' as a role, and that isn't selectable." % role)
        self.roles = roles
        assert isinstance(message, string_types)
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
        if send_email(request, subject = subject, recipients = self.email, html = html, send_immediately = True):
            self.sent_dates.append(utcnow())

    def claim(self, request):
        #Is the ticket open?
        if self.get_workflow_state() != 'open':
            raise HTTPForbidden("Access already granted with this ticket")
        #Find required resources and do some basic validation
        meeting = find_interface(self, IMeeting)
        assert meeting
        userid = request.authenticated_userid
        if userid is None:
            raise HTTPForbidden("You can't claim a ticket unless you're authenticated.")
        meeting.add_groups(userid, self.roles)
        self.claimed_by = userid
        self.set_workflow_state(request, 'closed')
        self.closed = utcnow()


def includeme(config):
    config.add_content_factory(InviteTicket)
