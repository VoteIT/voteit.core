
from voteit.core.models.site import SiteRoot
from voteit.core.models.users import Users
from voteit.core.models.user import User
from voteit.core import VoteITMF as _
from voteit.core.security import ROLE_ADMIN


def bootstrap_voteit():
    """ Bootstrap site root.
        Will add:
        - Site root
        - Users folder
        - An administrative user with login: admin and pass: admin
    """
    print "Bootstrapping site - creating 'admin' user with password 'admin'"
    root = SiteRoot()
    root.title = _(u"VoteIT")

    #Add users folder
    root['users'] = Users()
    users = root.users
    users.title = _(u"Registered users")
    
    #Add user admin
    admin = User()
    admin.set_password('admin')
    admin.set_field_value('first_name', 'Administrator')
    users['admin'] = admin
    
    #Add admin to group managers
    root.add_groups('admin', [ROLE_ADMIN])
    
    return root