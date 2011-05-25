import colander
from pyramid.security import Allow, Everyone, ALL_PERMISSIONS
from pyramid.security import DENY_ALL
from zope.interface import implements

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.base_content import BaseContent
from voteit.core.models.users import Users


class SiteRoot(BaseContent):
    """ The root of the site. Contains all other objects. """
    implements(ISiteRoot)
    content_type = 'SiteRoot'
    display_name = _(u"Site root")
    allowed_contexts = ()

    __acl__ = [(Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
               (Allow, security.ROLE_OWNER, (security.EDIT, security.CHANGE_PASSWORD)),
               (Allow, Everyone, security.VIEW),
               DENY_ALL]

    @property
    def users(self):
        return self['users']

def construct_schema(**kwargs):
    class SiteRootSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String())
        description = colander.SchemaNode(colander.String())
    return SiteRootSchema()


def includeme(config):
    from voteit.core import register_content_info
    register_content_info(construct_schema, SiteRoot, registry=config.registry)
