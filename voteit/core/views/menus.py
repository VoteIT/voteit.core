from arche.interfaces import IRoot
from arche.security import PERM_MANAGE_SYSTEM
from arche.views.base import BaseView
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config


@view_config(context=IRoot,
             permission=NO_PERMISSION_REQUIRED,
             name='_user_menu',
             renderer='voteit.core:templates/snippets/profile_menu.pt')
class UserMenu(BaseView):
    """ Profile / User menu """

    def __call__(self):
        return {}


@view_config(context=IRoot,
             permission=PERM_MANAGE_SYSTEM,
             name='_site_menu',
             renderer='voteit.core:templates/snippets/site_menu.pt')
class SiteMenu(BaseView):
    """ Site menu """

    def __call__(self):
        return {}
