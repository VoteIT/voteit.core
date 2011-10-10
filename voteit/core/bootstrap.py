from betahaus.pyracont.factories import createContent

from voteit.core import VoteITMF as _
from voteit.core.security import ROLE_ADMIN


def bootstrap_voteit(echo=True):
    """ Bootstrap site root.
        Will add:
        - Site root
        - Users folder
        - An administrative user with login: admin and pass: admin
    """
    from voteit.core.security import ROLE_OWNER

    if echo:
        print "Bootstrapping site - creating 'admin' user with password 'admin'"
    
    #Add root
    root = createContent('SiteRoot', title=_(u"VoteIT"))

    #Add users folder
    root['users'] = createContent('Users', title=_(u"Registered users"))
    users = root.users
    
    #Add user admin
    admin = createContent('User',
                          first_name = _(u'VoteIT'),
                          last_name = _(u'Administrator'))
    admin.set_password('admin')
    admin.add_groups('admin', (ROLE_OWNER,))
    users['admin'] = admin
    
    #Add admin to group managers
    root.add_groups('admin', [ROLE_ADMIN])
    
    return root
