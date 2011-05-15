import colander
from pyramid.security import Allow, Everyone, ALL_PERMISSIONS
from pyramid.security import DENY_ALL

from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.users import Users


class SiteRoot(BaseContent):
    """ The root of the site. Contains all other objects. """
    
    content_type = 'SiteRoot'

    omit_fields_on_edit = ()
    allowed_contexts = ()

    __acl__ = [(Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
               (Allow, security.ROLE_OWNER, (security.EDIT, security.CHANGE_PASSWORD)),
               (Allow, Everyone, security.VIEW),
               DENY_ALL]

    @property
    def users(self):
        return self['users']


class SiteRootSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())


def includeme(config):
    from voteit.core import register_content_info
    register_content_info(SiteRootSchema, SiteRoot, registry=config.registry)
