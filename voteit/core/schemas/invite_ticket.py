import colander
import deform

from voteit.core.validators import html_string_validator
from voteit.core.validators import multiple_email_validator
from voteit.core.schemas.common import strip_and_lowercase
from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.validators import deferred_token_form_validator


class ClaimTicketSchema(colander.Schema):
    validator = deferred_token_form_validator
    email = colander.SchemaNode(colander.String(),
                                title = _(u"Email address your invitation was sent to."),
                                validator = colander.Email(msg = _(u"Invalid email address.")),)
    #Note that validation for token depends on email, so it can't be set at field level.
    token = colander.SchemaNode(colander.String(),
                                title = _(u"claim_ticket_token_title",
                                          default = u"The access token your received in your email."),)

            
class AddTicketsSchema(colander.Schema):
    roles = colander.SchemaNode(
        colander.Set(),
        title = _(u"Roles"),
        default = (security.ROLE_VIEWER, security.ROLE_DISCUSS, security.ROLE_PROPOSE, security.ROLE_VOTER),
        description = _(u"add_tickets_roles_description",
                        default = u"""One user can have more than one role. Note that to be able to propose,
                        discuss and vote you need respective role. This is selected by default. If you want
                        to add a user that can only view, select View and uncheck everything else."""),
        widget = deform.widget.CheckboxChoiceWidget(values=security.MEETING_ROLES,),
    )
    emails = colander.SchemaNode(colander.String(),
                                 title = _(u"add_tickets_emails_titles",
                                           default=u"Email addresses to give the roles above."),
                                 description = _(u"add_tickets_emails_description",
                                                 default=u'Separate email addresses with a single line break.'),
                                 widget = deform.widget.TextAreaWidget(rows=7, cols=40),
                                 preparer = strip_and_lowercase,
                                 validator = colander.All(html_string_validator, multiple_email_validator),
    )
    message = colander.SchemaNode(colander.String(),
                                  title = _(u"Welcome text of the email that will be sent"),
                                  description = _(u"ticket_message_description",
                                                  default = u"The mail will contain instructions on how to access the meeting, "
                                                        u"so focus on anything that might be specific for your participants."),
                                  widget = deform.widget.TextAreaWidget(rows=5, cols=40),
                                  missing = u"",
                                  validator = html_string_validator,
    )


def includeme(config):
    config.add_content_schema('Meeting', AddTicketsSchema, 'add_tickets')
    config.add_content_schema('Meeting', ClaimTicketSchema, 'claim_ticket')
