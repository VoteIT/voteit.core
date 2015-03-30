from arche.api import Root
from arche.security import get_acl_registry
from zope.interface.declarations import implementer

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.base_content import BaseContent
from voteit.core.models.security_aware import SecurityAware


#FIXME: SiteRoot objects have used description as a text field for
#bulk text on the first page. They should be moved over to a new
#text field instead.


@implementer(ISiteRoot)
class SiteRoot(BaseContent, SecurityAware, Root):
    """ Site root content type - there's only one of these.
        See :mod:`voteit.core.models.interfaces.ISiteRoot`.
        All methods are documented in the interface of this class.
    """
    type_name = 'Root' #Arche compat
    schemas = {'edit':'SiteRootSchema'}

    @property
    def __acl__(self):
        aclreg = get_acl_registry()
        acl = []
        if self.allow_self_registration:
            acl.append((security.Allow, security.Everyone, security.REGISTER))
        acl.extend(aclreg.get_acl('Root:default'))
        return acl

    def __init__(self, data = None, **kwargs):
        super(SiteRoot, self).__init__(data = data, **kwargs)
        Root.__init__(self, data = data, **kwargs)

    @property
    def users(self):
        return self['users']

    @property
    def footer(self): #arche compat
        return self.get_field_value('footer', '')
    @footer.setter
    def footer(self, value):
        return self.set_field_value('footer', value)

    @property
    def support_email(self): #compat arche/voteit
        return self.get_field_value('support_email', '')
    @support_email.setter
    def support_email(self, value):
        return self.set_field_value('support_email', value)

    @property
    def head_title(self):
        """ The old voteit value for this is site_title. Arche calls it head_title."""
        return self.get_field_value('site_title', 'VoteIT')
    @head_title.setter
    def head_title(self, value):
        return self.set_field_value('site_title', value)


def includeme(config):
    config.add_content_factory(SiteRoot, addable_in = ('Meeting',))
    #Setup root acl
    aclreg = config.registry.acl
    root_acl = aclreg.new_acl('Root:default')
    root_acl.add(security.ROLE_ADMIN, security.ALL_PERMISSIONS)
    root_acl.add(security.ROLE_MEETING_CREATOR, security.ADD_MEETING)
    root_acl.add(security.Everyone, security.VIEW)
