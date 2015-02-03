from __future__ import unicode_literals

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from betahaus.pyracont.factories import createSchema

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
from voteit.core.views.base_view import BaseView


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


class UsersView(BaseView):
    """ Any regular view action without forms. """

  #  @view_config(context=IUser, renderer='templates/user.pt', permission=VIEW)
    def profile_view(self):
        return self.response

    @view_config(context=IUsers, renderer='templates/list_users.pt', permission=VIEW)
    def list_users(self):
        self.response['users'] = self.context.get_content(content_type = 'User', sort_on = 'userid')
        return self.response

    @view_config(context=IMeeting, name="_userinfo", permission=VIEW, xhr=True)
    def user_info_ajax_wrapper(self):
        return Response(self.user_info())

    @view_config(context=IMeeting, name="_userinfo", permission=VIEW, xhr=False, renderer="templates/simple_view.pt")
    def user_info_fallback(self):
        self.response['content'] = self.user_info()
        return self.response

    def user_info(self):
        """ Special view to allow other meeting participants to see information about a user
            who's in the same meeting as them.
            Normally called via AJAX and included in a popup or similar, but also a part of the
            users profile page.
            
            Note that a user might have participated within a meeting, and after that lost their
            permission. This view has to at least display the username of that person.
        """
        info_userid = self.request.GET['userid']
        if not info_userid in find_authorized_userids(self.context, (VIEW,)):
            msg = _(u"userid_not_registered_within_meeting_error",
                    default = u"Couldn't find any user with userid '${info_userid}' within this meeting.",
                    mapping = {'info_userid': info_userid})
            return self.api.translate(msg)
        user = self.api.get_user(info_userid)
        return self.api.render_view_group(user, self.request, 'user_info', api = self.api)
