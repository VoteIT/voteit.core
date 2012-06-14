from betahaus.pyracont.factories import createContent

from voteit.core import VoteITMF as _
from voteit.core.security import ROLE_ADMIN


def bootstrap_voteit(echo=True):
    """ Bootstrap site root.
        Will add:
        - Site root
        - Agenda template folder
        - Users folder
        - An administrative user with login: admin and pass: admin
    """

    if echo:
        print "Bootstrapping site - creating 'admin' user with password 'admin'"
    
    #Add root
    root = createContent('SiteRoot', title = _(u"VoteIT"), creators = ['admin'])

    #Add users folder
    root['agenda_templates'] = createContent('AgendaTemplates', title = _(u"Agenda templates"), creators = ['admin'])

    #Add users folder
    root['users'] = createContent('Users', title = _(u"Registered users"), creators = ['admin'])
    users = root.users
    
    #Add user admin - note that creators also set owner, which is important for changing password
    admin = createContent('User',
                          password = 'admin',
                          creators = ['admin'],
                          first_name = _(u'VoteIT'),
                          last_name = _(u'Administrator'))
    users['admin'] = admin
    
    #Add admin to group managers
    root.add_groups('admin', [ROLE_ADMIN])
    
    return root
