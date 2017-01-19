from arche.interfaces import ISchemaCreatedEvent
from arche.schemas import RootSchema
import colander
import deform

from voteit.core import _
from voteit.core.validators import richtext_validator


def root_schema_adjustments(schema, event):
    schema.add(colander.SchemaNode(
           colander.String(),
           missing = "",
           name = 'support_email',
           title = _(u"Support email for this site"),
           description = _(u"support_email_schema_desription",
                           default = u"This email will receive mail sent through the support "
                           "request form visible in the help menu."),
           validator = colander.Email(),) )
    schema.add(colander.SchemaNode(
           colander.String(),
           missing = "",
           name = 'body',
           title = _("Main body text"),
           description = _("main_body_desc",
                           default = "This is the first page of VoteIT. Describe your instance here."),
           widget = deform.widget.RichTextWidget(),
           validator = richtext_validator,) )


def includeme(config):
    config.add_subscriber(root_schema_adjustments, [RootSchema, ISchemaCreatedEvent])
