import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core.validators import html_string_validator
from voteit.core.validators import multiple_email_validator
from voteit.core import security
from voteit.core import VoteITMF as _


@schema_factory('ClaimTicketSchema')
class ClaimTicketSchema(colander.Schema):
    email = colander.SchemaNode(colander.String(),
                                title = _(u"Email address your invitation was sent to."),
                                validator = colander.Email(msg = _(u"Invalid email address.")),)
    #Note that validation for token depends on email, so it can't be set at field level.
    token = colander.SchemaNode(colander.String(),
                                title = _(u"The access token your received in your email."),)


            
@schema_factory('AddTicketsSchema')
class AddTicketsSchema(colander.Schema):
    roles = colander.SchemaNode(
        deform.Set(),
        title = _(u"Roles"),
        description = _(u'One user can have more than one role. Note that to be able to propose, discuss and vote the users needs to be participant AND voter.'),
        widget = deform.widget.CheckboxChoiceWidget(values=security.MEETING_ROLES,),
    )
    #FIXME: Validate that an invite doesn't already exist.
    #FIXME: Add custom subject line. No sense in having it static!
    emails = colander.SchemaNode(colander.String(),
                                 title = _(u"Email addresses to give the role above."),
                                 description = _(u'Separate email adresses with a single line break'),
                                 widget = deform.widget.TextAreaWidget(rows=7, cols=40),
                                 validator = colander.All(html_string_validator, multiple_email_validator),
    )
    message = colander.SchemaNode(colander.String(),
                                  title = _(u'Welcome text of the email that will be sent'),
                                  description = _(u'No HTML tags allowed.'),
                                  widget = deform.widget.TextAreaWidget(rows=5, cols=40),
                                  default = _('invitation_default_text',
                                              default=u"You've received a meeting invitation for a VoteIT meeting."),
                                  missing = u'',
                                  validator = html_string_validator,
    )
    

@colander.deferred
def checkbox_of_invited_emails_widget(node, kw):
    context = kw['context']
    email_choices = [(x.email, x.email) for x in context.invite_tickets.values() if x.get_workflow_state() != u'closed']
    return deform.widget.CheckboxChoiceWidget(values=email_choices)


@schema_factory('ManageTicketsSchema')
class ManageSchema(colander.Schema):
    emails = colander.SchemaNode(
        deform.Set(),
        widget = checkbox_of_invited_emails_widget,
        title = _(u"Current invitations"),
    )
