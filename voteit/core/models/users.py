import colander
from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import DENY_ALL

from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers
from voteit.core.validators import html_string_validator
from voteit.core import security


class Users(BaseContent):
    """ Container for all user objects """
    implements(IUsers)
    content_type = 'Users'
    display_name = _(u"Users")
    allowed_contexts = ()
    add_permission = None

    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, security.VIEW, security.ADD_USER)),
               DENY_ALL]

    def get_user_by_email(self, email):
        for user in self.get_content(iface=IUser):
            if user.get_field_value('email') == email:
                return user


def construct_schema(**kwargs):
    class UsersSchema(colander.Schema):
        title = colander.SchemaNode(colander.String(),
            validator=html_string_validator,)
        description = colander.SchemaNode(colander.String(),
            validator=html_string_validator,)
    return UsersSchema()


def includeme(config):
    from voteit.core.app import register_content_info
    register_content_info(construct_schema, Users, registry=config.registry)
