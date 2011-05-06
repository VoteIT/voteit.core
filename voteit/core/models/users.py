from voteit.core.models.base_content import BaseContent
import colander


class Users(BaseContent):
    """ Container for all user objects """
    content_type = 'Users'
    omit_fields_on_edit = ()
    allowed_contexts = ()
    add_permission = None
    

class UsersSchema(colander.Schema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
