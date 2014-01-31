from urllib import unquote

import deform
import httpagentparser
from decimal import Decimal
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.security import remember
from pyramid.security import forget
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.renderers import render
from betahaus.pyracont.factories import createSchema
from betahaus.viewcomponent.interfaces import IViewGroup

from voteit.core import security
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IAuthPlugin
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_login
from voteit.core.models.schemas import button_register
from voteit.core.views.base_edit import BaseEdit
from voteit.core import VoteITMF as _
from voteit.core.events import LoginSchemaCreated
from voteit.core.events import RegisterSchemaCreated


class AuthView(BaseEdit):

    def browser_check(self):
        """ Will redirect to an error page if an unsupported browser is used. """
        browser_name = u''
        browser_version = 0
        try:
            user_agent = httpagentparser.detect(self.request.user_agent)
            browser_name = user_agent['browser']['name']
            browser_version = Decimal(user_agent['browser']['version'][0:user_agent['browser']['version'].find('.')])
        except:
            pass
        #FIXME: maybe this definition should be somewhere else
        #FIXME: This will break easilly and should have a try except
        if browser_name == u'Microsoft Internet Explorer' and browser_version < Decimal(8):
            url = self.request.resource_url(self.context, 'unsupported_browser')
            return HTTPFound(location=url)

    def login_from_method(self, method_name):
        auth_method = self.request.registry.getMultiAdapter((self.context, self.request),
                                                            IAuthPlugin, name = method_name)
        schema = createSchema('LoginSchema')
        add_csrf_token(self.context, self.request, schema)
        event = LoginSchemaCreated(schema, auth_method)
        self.request.registry.notify(event)
        schema = schema.bind(context = self.context, request = self.request, api = self.api)
        action_url = self.request.resource_url(self.context, 'login', query = {'method': method_name})
        form = deform.Form(schema, buttons = (button_login,), action = action_url)
        POST = self.request.POST
        if 'login' in POST:
            controls = POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            return auth_method.login(appstruct)
        self.response['form'] = form.render()
        return self.response

    @view_config(name = 'login', renderer = "templates/login.pt", permission = NO_PERMISSION_REQUIRED, request_method = "GET")
    def login_main(self):
        default_auth = self.request.registry.settings['voteit.default_auth']
        #render_login_info
        alternative_methods = []
        for (name, auth_plugin) in self.request.registry.getAdapters((self.context, self.request), IAuthPlugin):
            if name == default_auth:
                continue
            result = auth_plugin.render_login_info()
            if not result:
                result = render("templates/snippets/default_auth_button.pt",
                                {'auth_plugin': auth_plugin},
                                request = self.request)
            alternative_methods.append(result)
        self.response['alternative_methods'] = alternative_methods
        return self.login_from_method(default_auth)

    @view_config(name = 'login', renderer = "templates/base_edit.pt", permission = NO_PERMISSION_REQUIRED, request_method = "POST")
    def login_alternate(self):
        browser_check_result = self.browser_check()
        if browser_check_result:
            return browser_check_result
        method_name = self.request.GET.get('method')
        if not method_name:
            return HTTPFound(location = self.request.resource_url(self.api.root, 'login'))
        return self.login_from_method(method_name)

    @view_config(name ="register", renderer = "templates/register.pt", permission = NO_PERMISSION_REQUIRED)
    def register_main(self):
        browser_check_result = self.browser_check()
        if browser_check_result:
            return browser_check_result
        

    @view_config(route_name = 'register', renderer = "templates/base_edit.pt", permission  = NO_PERMISSION_REQUIRED)
    def register(self):
        browser_check_result = self.browser_check()
        if browser_check_result:
            return browser_check_result
        method_name = self.request.matchdict.get('method')
        auth_method = self.request.registry.getMultiAdapter((self.context, self.request), IAuthPlugin, name = method_name)
        schema = createSchema('RegisterSchema')
        add_csrf_token(self.context, self.request, schema)
        event = RegisterSchemaCreated(schema, auth_method)
        self.request.registry.notify(event)
        schema = schema.bind(context = self.context, request = self.request, api = self.api)
        form = deform.Form(schema, buttons=(button_register,))
        POST = self.request.POST
        if 'register' in POST:
            controls = POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            came_from = unquote(appstruct.pop('came_from'))
            if came_from == u'/':
                came_from = None
            obj = auth_method.register(appstruct)
            assert IUser.providedBy(obj)
            headers = remember(self.request, obj.userid)  # login user
            if came_from:
                url = came_from
                msg = _(u"You're now registered. Welcome!")
            else:
                url = self.request.resource_url(obj)
                msg = _(u"joined_without_ticket_intro_text",
                        default = u"You're now registered. Welcome! "
                                  u"Please take some time to update your profile and write something about yourself. "
                                  u"To join a meeting, you need to either have an invitaion that will have been sent "
                                  u"to you via email, or the url of a meeting to request access to it.")            
            self.api.flash_messages.add(msg)
            return HTTPFound(location = url, headers = headers)
        
        #Adjust appstruct to include any default values that might have been passed along
        appstruct = auth_method.register_appstruct(self.context, self.request, schema)
        self.response['form'] = form.render(appstruct = appstruct)
        return self.response

    @view_config(context=ISiteRoot, name='logout', permission = NO_PERMISSION_REQUIRED)
    def logout(self):
        headers = forget(self.request)
        return HTTPFound(location = self.request.resource_url(self.context),
                         headers = headers)
