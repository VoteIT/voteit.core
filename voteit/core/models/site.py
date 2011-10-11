from pyramid.security import Allow
from pyramid.security import Everyone
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import DENY_ALL
from zope.interface import implements
from repoze.catalog.catalog import Catalog
from repoze.catalog.document import DocumentMap
from betahaus.pyracont.decorators import content_factory

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.base_content import BaseContent
from voteit.core.models.catalog import update_indexes


@content_factory('SiteRoot', title=_(u"Site root"))
class SiteRoot(BaseContent):
    """ The root of the site. Contains all other objects. """
    implements(ISiteRoot)
    content_type = 'SiteRoot'
    display_name = _(u"Site root")
    allowed_contexts = ()
    schemas = {'edit':'SiteRootSchema'}

    __acl__ = [(Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
               (Allow, security.ROLE_OWNER, (security.EDIT, security.CHANGE_PASSWORD, )),
               (Allow, Everyone, (security.VIEW, security.ADD_MEETING)),
               DENY_ALL]

    def __init__(self, **kwargs):
        super(SiteRoot, self).__init__(**kwargs)
        self.catalog = Catalog()
        self.catalog.__parent__ = self #To make traversal work
        self.catalog.document_map = DocumentMap()
        update_indexes(self.catalog)

    @property
    def users(self):
        return self['users']
