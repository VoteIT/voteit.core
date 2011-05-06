import colander
from pyramid.security import Allow
from pyramid.security import DENY_ALL

from voteit.core.models.base_content import BaseContent
from voteit.core.models.users import Users

from voteit.core import security


class SiteRoot(BaseContent):
    """ The root of the site. Contains all other objects. """
    
    content_type = 'SiteRoot'

    omit_fields_on_edit = ()
    allowed_contexts = ()

    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, )),
               (Allow, security.ROLE_ADMIN, security.ALL_ADD_PERMISSIONS),
               (Allow, security.ROLE_OWNER, (security.EDIT, )),
               DENY_ALL]

    @property
    def users(self):
        return self['users']


class SiteRootSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
