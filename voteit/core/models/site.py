import colander
import deform

from pyramid.security import Allow, Everyone, ALL_PERMISSIONS
from pyramid.security import DENY_ALL
from zope.interface import implements
from repoze.catalog.catalog import Catalog
from repoze.catalog.document import DocumentMap

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.base_content import BaseContent
from voteit.core.models.users import Users
from voteit.core.validators import html_string_validator
from voteit.core.models.catalog import update_indexes


class SiteRoot(BaseContent):
    """ The root of the site. Contains all other objects. """
    implements(ISiteRoot)
    content_type = 'SiteRoot'
    display_name = _(u"Site root")
    allowed_contexts = ()

    __acl__ = [(Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
               (Allow, security.ROLE_OWNER, (security.EDIT, security.CHANGE_PASSWORD, )),
               (Allow, Everyone, security.VIEW),
               DENY_ALL]

    def __init__(self):
        self.catalog = Catalog()
        self.catalog.__parent__ = self #To make traversal work
        self.catalog.document_map = DocumentMap()
        update_indexes(self.catalog)
        super(SiteRoot, self).__init__()

    @property
    def users(self):
        return self['users']

def construct_schema(**kwargs):
    class SiteRootSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String())
        description = colander.SchemaNode(colander.String(),
                                          missing = u"",
                                          widget=deform.widget.RichTextWidget())
        
    return SiteRootSchema()


def includeme(config):
    from voteit.core.app import register_content_info
    register_content_info(construct_schema, SiteRoot, registry=config.registry)
