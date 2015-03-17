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


# @view_config(context = IUser,
#              name = "manage_connections",
#              renderer = DEFAULT_TEMPLATE,
#              permission = EDIT)
# class ManageConnectedProfilesForm(BaseForm):
#     """ Currently only remove functionality. This should change.
#     """
#     buttons = (button_delete, button_cancel)
# 
#     def get_schema(self): return createSchema('ManageConnectedProfilesSchema')
# 
#     def appstruct(self): return {}
# 
#     def delete_success(self, appstruct):
#         domains = appstruct['auth_domains']
#         if domains:
#             for domain in domains:
#                 del self.context.auth_domains[domain]
#             msg = _(u"Removing information for: ${domains}",
#                     mapping = {'domains': ", ".join(domains)})
#             self.api.flash_messages.add(msg)
#         else:
#             self.api.flash_messages.add(_(u"Nothing updated"))
#         return HTTPFound(location = self.request.resource_url(self.context))
