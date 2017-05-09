from arche.interfaces import IRoot
from arche.views.base import BaseView
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config


@view_config(context=IRoot,
             permission=NO_PERMISSION_REQUIRED,
             name='_user_menu',
             renderer='voteit.core:templates/snippets/profile_menu.pt')
class UserMenu(BaseView):

    def __call__(self):
        return {}
