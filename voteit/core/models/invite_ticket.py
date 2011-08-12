import string
from random import choice

import colander
import deform
from zope.component import getUtility
from zope.interface import implements
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.traversal import find_interface
from pyramid.url import resource_url
from pyramid.exceptions import Forbidden
from pyramid.security import authenticated_userid
from persistent import Persistent

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IInviteTicket
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.workflow_aware import WorkflowAware
from voteit.core.validators import html_string_validator
from voteit.core.models.date_time_util import utcnow

SELECTABLE_ROLES = (security.ROLE_MODERATOR,
                    security.ROLE_PARTICIPANT,
                    security.ROLE_VOTER,
                    security.ROLE_VIEWER,
                    )


class InviteTicket(Persistent, WorkflowAware):
    """ Invite ticket. Send these to give access to new users.
        See IInviteTicket for more info.
    """
    implements(IInviteTicket)
    content_type = 'InviteTicket'
    allowed_contexts = () #Not addable through regular forms
    add_permission = None
    
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

    def send(self, request):
        """ Send message about invite ticket. """

        meeting = find_interface(self, IMeeting)
        assert meeting
        
        form_url = "%sticket" % resource_url(meeting, request)
        access_link = form_url + '?email=%s&token=%s' % (self.email, self.token)
        
        #FIXME: Proper template or edit form
        instructions = """


-------------------------------------------------------------

To access the meeting, you need to do the following:
1. You need to register an account at the site inviting you.
2. Log in
3. Click the link below to gain access directly, or go to:
   %s
   and enter your details

Access link for direct acces once you've logged in:
%s
        
        """ % (form_url, access_link)
        
        sender = meeting.get_field_value('meeting_mail_address')
        body = self.message + instructions

        msg = Message(subject=_(u"VoteIT meeting invitation"),
                      sender = sender and sender or None,
                      recipients=[self.email],
                      body=body)

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


def construct_schema(context=None, request=None, type=None):

    if type == 'claim':
        class ClaimSchema(colander.Schema):
            email = colander.SchemaNode(colander.String(),
                                        title = _(u"Email address your invitation was sent to."),
                                        validator = colander.Email(msg = _(u"Invalid email address.")),)
            #Note that validation for token depends on email, so it can't be set at field level.
            token = colander.SchemaNode(colander.String(),
                                        title = _(u"The access token your received in your email."),)
        
        def token_validator(form, value):
            value['email']
            value['token']
            
            token = context.invite_tickets.get(value['email'])
            if not token:
                exc = colander.Invalid(form, 'Incorrect email')
                exc['token'] = _(u"Couldn't find any invitation for this email address.")
                raise exc
            
            if token.token != value['token']:
                exc = colander.Invalid(form, _(u"Email matches, but token doesn't"))
                exc['token'] = _(u"Check this field - token doesn't match")
                raise exc

        return ClaimSchema(validator = token_validator)
            
    
    if type == 'add':
        class AddSchema(colander.Schema):
            roles = colander.SchemaNode(
                deform.Set(),
                title = _(u"Roles"),
                widget = deform.widget.CheckboxChoiceWidget(values=security.MEETING_ROLES,),
            )
            #FIXME: Proper validation or even a list of emails widget.
            #FIXME: Validate that an invite doesn't already exist.
            emails = colander.SchemaNode(colander.String(),
                                         title = _(u"Email addresses to give the role above."),
                                         widget = deform.widget.TextAreaWidget(rows=5, cols=40),
                                         validator = html_string_validator,
            )
            message = colander.SchemaNode(colander.String(),
                                          title = _(u'Welcome text of the email that will be sent'),
                                          description = _(u'No HTML tags allowed.'),
                                          widget = deform.widget.TextAreaWidget(rows=5, cols=40),
                                          default = _(u"You've received a meeting invitation for a VoteIT meeting."),
                                          missing = u'',
                                          validator = html_string_validator,
            )
                                       
        return AddSchema()
    
    if type == 'manage':
        email_choices = [(x.email, x.email) for x in context.invite_tickets.values() if x.get_workflow_state() != u'closed']
        class ManageSchema(colander.Schema):
            emails = colander.SchemaNode(
                deform.Set(),
                widget = deform.widget.CheckboxChoiceWidget(values=email_choices),
                title = _(u"Current invitations"),
                validator = html_string_validator,
            )
        return ManageSchema()



def includeme(config):
    from voteit.core.app import register_content_info
    register_content_info(construct_schema, InviteTicket, registry=config.registry)
