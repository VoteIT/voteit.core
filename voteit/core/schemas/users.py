import colander
from betahaus.pyracont.decorators import schema_factory

from voteit.core.validators import html_string_validator


@schema_factory('UsersSchema')
class UsersSchema(colander.Schema):
    title = colander.SchemaNode(colander.String(),
        validator=html_string_validator,)
    description = colander.SchemaNode(colander.String(),
        validator=html_string_validator,)