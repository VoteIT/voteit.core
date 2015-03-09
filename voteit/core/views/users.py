from __future__ import unicode_literals

from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from betahaus.pyracont.factories import createSchema
from arche.views.base import BaseView
from betahaus.viewcomponent import render_view_group

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_change
from voteit.core.models.schemas import button_delete
from voteit.core.models.schemas import button_request
from voteit.core.security import CHANGE_PASSWORD
from voteit.core.security import EDIT
from voteit.core.security import MANAGE_SERVER
from voteit.core.security import VIEW
from voteit.core.security import find_authorized_userids
from voteit.core.views.base_edit import BaseForm
#from voteit.core.views.base_view import BaseView


DEFAULT_TEMPLATE = "voteit.core:views/templates/base_edit.pt"


#@view_config(context = IUser,
#             name = "change_password",
#             renderer = DEFAULT_TEMPLATE,
#             permission = CHANGE_PASSWORD)
class ChangePasswordForm(BaseForm):
    """ Change password form.
    
        Default behaviour:
            User changes their own password and have
            to submit their old password first.

        Admin behaviour:
            Admin may change another users password directly. For their own password,
            the same rule as normal users applies.
    """
    buttons = (button_change, button_cancel)

    def appstruct(self): return {}

    def get_schema(self):
        if self.context != self.api.user_profile and self.api.context_has_permission(MANAGE_SERVER, self.api.root):
            return createSchema('ChangePasswordAdminSchema')
        return createSchema('ChangePasswordSchema')

    def change_success(self, appstruct):
        self.context.set_password(appstruct['password'])            
        msg = _(u"Password changed")
        self.api.flash_messages.add(msg)
        return HTTPFound(location = self.request.resource_url(self.context))



#@view_config(context = ISiteRoot,
#             name = 'request_password',
#             renderer = DEFAULT_TEMPLATE,
#             permission = NO_PERMISSION_REQUIRED)
class RequestPasswordForm(BaseForm):
    """ Email a change password token to a users registered email address.
    """
    buttons = (button_request, button_cancel)

    def get_schema(self): return createSchema('RequestNewPasswordSchema')

    def appstruct(self): return {}

    def request_success(self, appstruct):
        #Validation performed by schema so this should be safe
        userid_or_email = appstruct['userid_or_email']
        if '@' in userid_or_email:
            #assume email
            user = self.context['users'].get_user_by_email(userid_or_email)
        else:
            user = self.context['users'].get(userid_or_email)
        user.new_request_password_token(self.request)
        msg = _('reset_pw_sent_msg',
                default = 'An email with a link to reset your password has been sent.')
        self.api.flash_messages.add(msg)
        return HTTPFound(location = self.request.resource_url(self.api.root))


#@view_config(context = IUser,
#             name = "token_pw",
#             renderer = DEFAULT_TEMPLATE,
#             permission = NO_PERMISSION_REQUIRED)
class TokenChangePasswordForm(BaseForm):
    """ When a user has requested a change password link.
        Note that there's no permisison check here since the token from
        the email determines if this is allowed or not.
        
        The token itself is validated by the schema.
    """
    buttons = (button_change, button_cancel)

    def get_schema(self): return createSchema('TokenPasswordChangeSchema')

    def appstruct(self): return {'token': self.request.GET.get('token', '')}

    def change_success(self, appstruct):
        self.context.remove_password_token()
        self.context.set_password(appstruct['password'])
        self.api.flash_messages.add(_(u"Password set. You may login now."))
        return HTTPFound(location = self.request.resource_url(self.api.root, 'login'))


@view_defaults(context = IUser, permission = VIEW)
class UserView(BaseView):

    @view_config(renderer = "voteit.core:templates/user.pt")
    def profile(self):
        return {'userinfo': render_view_group(self.context, self.request, 'user_info', view = self)}


@view_config(context = IUser,
             name = "manage_connections",
             renderer = DEFAULT_TEMPLATE,
             permission = EDIT)
class ManageConnectedProfilesForm(BaseForm):
    """ Currently only remove functionality. This should change.
    """
    buttons = (button_delete, button_cancel)

    def get_schema(self): return createSchema('ManageConnectedProfilesSchema')

    def appstruct(self): return {}

    def delete_success(self, appstruct):
        domains = appstruct['auth_domains']
        if domains:
            for domain in domains:
                del self.context.auth_domains[domain]
            msg = _(u"Removing information for: ${domains}",
                    mapping = {'domains': ", ".join(domains)})
            self.api.flash_messages.add(msg)
        else:
            self.api.flash_messages.add(_(u"Nothing updated"))
        return HTTPFound(location = self.request.resource_url(self.context))
