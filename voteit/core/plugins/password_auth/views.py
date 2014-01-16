from pyramid.view import view_config
from deform import Form
from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.renderers import render
from betahaus.pyracont.factories import createSchema
from betahaus.viewcomponent import view_action

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IAuthPlugin
from voteit.core.events import LoginSchemaCreated
from voteit.core.security import CHANGE_PASSWORD
from voteit.core.security import MANAGE_SERVER
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_change
from voteit.core.models.schemas import button_request
from voteit.core.models.schemas import button_update
from voteit.core.models.schemas import button_login
from voteit.core.views.base_view import BaseView


DEFAULT_TEMPLATE = "voteit.core:views/templates/base_edit.pt"


class PasswordAuthView(BaseView):

    @view_config(context = IUser, name = "change_password", renderer = DEFAULT_TEMPLATE, permission = CHANGE_PASSWORD)
    def password_form(self):
        # if admin is changing password for another user no verification of current password is needed
        if self.context != self.api.user_profile and self.api.context_has_permission(MANAGE_SERVER, self.api.root):
            schema = createSchema('ChangePasswordAdminSchema')
        else:
            schema = createSchema('ChangePasswordSchema')
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context = self.context, request = self.request, api = self.api)
        form = Form(schema, buttons = (button_update, button_cancel))
        self.api.register_form_resources(form)
        post = self.request.POST
        if 'update' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            self.context.set_password(appstruct['password'])
            msg = _(u"Password changed")
            self.api.flash_messages.add(msg)
            url = self.request.resource_url(self.context)
            return HTTPFound(location = url)
        if 'cancel' in post:
            url = self.request.resource_url(self.context)
            return HTTPFound(location = url)
        #No action - Render edit form
        self.response['form'] = form.render()
        return self.response

    @view_config(context = IUser, name = "token_pw", renderer = DEFAULT_TEMPLATE, permission = NO_PERMISSION_REQUIRED)
    def token_password_change(self):
        schema = createSchema('TokenPasswordChangeSchema')
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context = self.context, request = self.request, api = self.api)
        form = Form(schema, buttons = (button_change, button_cancel))
        self.api.register_form_resources(form)
        post = self.request.POST
        if 'change' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            self.context.remove_password_token()
            self.context.set_password(appstruct['password'])
            self.api.flash_messages.add(_(u"Password set. You may login now."))
            url = self.request.resource_url(self.api.root, 'login', 'password')
            return HTTPFound(location = url)
        if 'cancel' in post:
            url = self.request.resource_url(self.api.root)
            return HTTPFound(location = url)
        #Fetch token from get request
        token = self.request.GET.get('token', None)
        if token is None:
            msg = _(u"Invalid security token. Did you click the link in your email?")
            self.api.flash_messages.add(msg, type = "error")
            url = self.request.resource_url(self.api.root)
            return HTTPFound(location = url)
        #Everything seems okay. Render form
        appstruct = dict(token = token)
        self.response['form'] = form.render(appstruct = appstruct)
        return self.response

    @view_config(context = ISiteRoot, name = 'request_password',
                 renderer = DEFAULT_TEMPLATE, permission = NO_PERMISSION_REQUIRED)
    def request_password(self):        
        schema = createSchema('RequestNewPasswordSchema')
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context = self.context, request = self.request, api = self.api)
        form = Form(schema, buttons = (button_request, button_cancel))
        self.api.register_form_resources(form)
        if 'request' in self.request.POST:
            controls = self.request.POST.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            userid_or_email = appstruct['userid_or_email']
            #userid here can be either an email address or a login name
            if '@' in userid_or_email:
                #assume email
                user = self.context['users'].get_user_by_email(userid_or_email)
            else:
                user = self.context['users'].get(userid_or_email)
            if IUser.providedBy(user):
                user.new_request_password_token(self.request)
                self.api.flash_messages.add(_('Email sent.'))
                url = self.request.resource_url(self.api.root)
                return HTTPFound(location = url)
            self.api.flash_messages.add(_('Username or email not found.'), type = 'error')
        if 'cancel' in self.request.POST:
            url = self.request.resource_url(self.api.root)
            return HTTPFound(location = url)
        #Render form
        self.response['form'] = form.render()
        return self.response


@view_action('sidebar', 'login_pw')
def login_box(context, request, va, **kwargs):
    api = kwargs['api']
    if api.userid:
        return u""
    auth_method = request.registry.queryMultiAdapter((context, request), IAuthPlugin, name = 'password')
    schema = createSchema('LoginSchema')
    add_csrf_token(context, request, schema)
    event = LoginSchemaCreated(schema, auth_method)
    request.registry.notify(event)
    schema = schema.bind(context = context, request = request, api = api)
    action_url = request.resource_url(api.root, 'login', 'password')
    form = Form(schema, buttons = (button_login,), action = action_url)
    api.register_form_resources(form)
    response = dict(
        api = api,
        form = form.render(),
    )
    return render('login_pw.pt', response, request = request)
