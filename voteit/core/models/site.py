from arche.api import Root
from zope.interface.declarations import implementer

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.base_content import BaseContent
from voteit.core.models.security_aware import SecurityAware


_DEFAULT_ACL = ((security.Allow, security.ROLE_ADMIN, security.ALL_PERMISSIONS),
                (security.Allow, security.ROLE_MEETING_CREATOR, security.ADD_MEETING),
                (security.Allow, security.Everyone, security.VIEW),
                security.DENY_ALL)


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
        if self.allow_self_registration:
            acl.append((security.Allow, security.Everyone, security.REGISTER))
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
