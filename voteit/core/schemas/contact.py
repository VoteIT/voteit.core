import colander
import deform

from voteit.core.validators import no_html_validator
from voteit.core.schemas.common import deferred_default_user_fullname
from voteit.core.schemas.common import deferred_default_user_email
from voteit.core import _


@colander.deferred
def deferred_meeting_title(node, kw):
    context = kw['context']
    if context.content_type == 'Meeting':
        return context.title
    return u""


class SupportSchema(colander.Schema):
    """ Support contact form schema. """
    title = _("Support request")
    name = colander.SchemaNode(colander.String(),
                               title = _(u"Name"),
                               default = deferred_default_user_fullname,
                               validator = colander.Length(max = 100),)
    email = colander.SchemaNode(colander.String(),
                               title = _(u"Email"),
                               description = _(u"contact_schema_email_description",
                                               default = u"Leave this field empty if you want to be anonymous. Remember that you won't be able to receive a reply if it's empty!"),
                               default = deferred_default_user_email,
                               validator = colander.Email(),
                               missing=u"") 
    subject = colander.SchemaNode(colander.String(),
                                  title = _(u"Subject"),
                                  validator = no_html_validator,)
    meeting_title = colander.SchemaNode(colander.String(),
                                        title = _(u"Meeting"),
                                        description = _(u"support_schema_meeting_description",
                                                        default = u"Is this support request about a specific meeting? "
                                                            u"In that case, what's the title of the meeting? "
                                                            u"(It doesn't have to be exact, it's just so we know what to look for!)"),
                                        default = deferred_meeting_title,
                                        validator = no_html_validator,
                                        missing = u"",)
    message = colander.SchemaNode(colander.String(),
                                  title = _(u'What do you need help with?'),
                                  description = _(u"support_schema_message_description",
                                                  default = u"Please take time to describe what you need help with, or what went wrong. "
                                                            u"If you're submitting an error report, please explain what you were doing and how we can reproduce the error. "
                                                            u"The more information you send us, the better. We're really bad at reading minds..."),
                                  widget = deform.widget.TextAreaWidget(rows=10, cols=40),
                                  validator = no_html_validator,)


def includeme(config):
    config.add_content_schema('Root', SupportSchema, 'support')
    config.add_content_schema('Meeting', SupportSchema, 'support')
