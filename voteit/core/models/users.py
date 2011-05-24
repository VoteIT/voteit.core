import colander
from zope.interface import implements

from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers


class Users(BaseContent):
    """ Container for all user objects """
    implements(IUsers)
    content_type = 'Users'
    omit_fields_on_edit = ()
    allowed_contexts = ()
    add_permission = None
    
    def get_user_by_email(self, email):
        for user in self.get_content(iface=IUser):
            if user.get_field_value('email') == email:
                return user


def construct_schema(**kwargs):
    class UsersSchema(colander.Schema):
        title = colander.SchemaNode(colander.String())
        description = colander.SchemaNode(colander.String())
    return UsersSchema()


def includeme(config):
    from voteit.core import register_content_info
    register_content_info(construct_schema, Users, registry=config.registry)
