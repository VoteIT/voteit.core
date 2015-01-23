from arche.api import Root
from betahaus.pyracont.decorators import content_factory
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.security import DENY_ALL
from pyramid.security import Everyone
from repoze.catalog.catalog import Catalog
from repoze.catalog.document import DocumentMap
from zope.interface import implements
from zope.interface.declarations import implementer

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.base_content import BaseContent
#from voteit.core.models.catalog import update_indexes
from voteit.core.models.security_aware import SecurityAware


_DEFAULT_ACL = ((Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
                (Allow, security.ROLE_MEETING_CREATOR, security.ADD_MEETING),
                (Allow, Everyone, security.VIEW),
                DENY_ALL)


#@content_factory('SiteRoot', title=_(u"Site root"))
@implementer(ISiteRoot)
class SiteRoot(BaseContent, SecurityAware, Root):
    """ Site root content type - there's only one of these.
        See :mod:`voteit.core.models.interfaces.ISiteRoot`.
        All methods are documented in the interface of this class.
    """
    type_name = 'Root' #Arche compat
    schemas = {'edit':'SiteRootSchema'}
    footer = ""

    @property
    def __acl__(self):
        acl = []
        if self.get_field_value('allow_add_meeting', False):
            acl.append((Allow, Authenticated, (security.ADD_MEETING, )))
        acl.extend(_DEFAULT_ACL)
        return acl

    def __init__(self, data = None, **kwargs):
        super(SiteRoot, self).__init__(data = data, **kwargs)
        Root.__init__(self, data = data, **kwargs)

    @property
    def users(self):
        return self['users']

def includeme(config):
    config.add_content_factory(SiteRoot, addable_in = ('Meeting',))
