from arche.interfaces import ISchemaCreatedEvent
from arche.schemas import RootSchema
import colander

from voteit.core import _


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


def includeme(config):
    config.add_subscriber(root_schema_adjustments, [RootSchema, ISchemaCreatedEvent])
