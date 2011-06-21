from pyramid.threadlocal import get_current_registry

from voteit.core import VoteITMF as _
from voteit.core.security import ROLE_ADMIN
from voteit.core.models.interfaces import IContentUtility, ISQLSession


def bootstrap_voteit(registry=None, echo=True):
    """ Bootstrap site root.
        Will add:
        - Site root
        - Users folder
        - An administrative user with login: admin and pass: admin
    """
    if registry is None:
        registry = get_current_registry()
    
    content_util = registry.getUtility(IContentUtility)

    if echo:
        print "Bootstrapping site - creating 'admin' user with password 'admin'"
    
    #Add root
    root = content_util['SiteRoot'].type_class()
    root.title = _(u"VoteIT")

    #Add users folder
    root['users'] = content_util['Users'].type_class()
    users = root.users
    users.title = _(u"Registered users")
    
    #Add user admin
    admin = content_util['User'].type_class()
    admin.set_password('admin')
    admin.set_field_value('first_name', _(u'VoteIT'))
    admin.set_field_value('last_name', _(u'Administrator'))
    users['admin'] = admin
    
    #Add admin to group managers
    root.add_groups('admin', [ROLE_ADMIN])
    
    return root
