import colander
from zope.interface import implements

from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUsers


class Users(BaseContent):
    """ Container for all user objects """
    implements(IUsers)
    content_type = 'Users'
    omit_fields_on_edit = ()
    allowed_contexts = ()
    add_permission = None
    

class UsersSchema(colander.Schema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())


def includeme(config):
    from voteit.core import register_content_info
    register_content_info(UsersSchema, Users, registry=config.registry)
