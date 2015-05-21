from __future__ import unicode_literals

from arche.views.base import BaseView
from betahaus.viewcomponent import render_view_group
from pyramid.view import view_config
from pyramid.view import view_defaults

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IUser
from voteit.core.security import VIEW


DEFAULT_TEMPLATE = "voteit.core:views/templates/base_edit.pt"


@view_defaults(context = IUser, permission = VIEW)
class UserView(BaseView):

    @view_config(renderer = "voteit.core:templates/user.pt")
    def profile(self):
        return {'userinfo': render_view_group(self.context, self.request, 'user_info', view = self)}
