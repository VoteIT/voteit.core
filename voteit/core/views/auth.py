import httpagentparser
from decimal import Decimal
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.renderers import render

from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IAuthPlugin
from voteit.core.views.base_edit import BaseEdit


class AuthView(BaseEdit):

    def browser_check(self):
        """ Will redirect to an error page if an unsupported browser is used. """
        browser_name = u''
        browser_version = 0
        try:
            user_agent = httpagentparser.detect(self.request.user_agent)
            browser_name = user_agent['browser']['name']
            browser_version = Decimal(user_agent['browser']['version'][0:user_agent['browser']['version'].find('.')])
        except Exception:
            pass
        #FIXME: maybe this definition should be somewhere else
        #FIXME: This will break easilly and should have a try except
        if browser_name == u'Microsoft Internet Explorer' and browser_version < Decimal(8):
            url = self.request.resource_url(self.context, 'unsupported_browser')
            return HTTPFound(location=url)

    def login_from_method(self, method_name):
        auth_method = self.request.registry.getMultiAdapter((self.context, self.request), IAuthPlugin, name = method_name)
        return auth_method.render_login(self.api, self.response)

    @view_config(name = 'login', renderer = "templates/login.pt", permission = NO_PERMISSION_REQUIRED, request_method = "GET")
    def login(self):
        browser_check_result = self.browser_check()
        if browser_check_result:
            return browser_check_result
        default_auth = self.request.registry.settings['voteit.default_auth']
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
        default_auth = self.request.registry.settings['voteit.default_auth']
        alternative_methods = []
        for (name, auth_plugin) in self.request.registry.getAdapters((self.context, self.request), IAuthPlugin):
            if name == default_auth:
                continue
            result = auth_plugin.render_register_info()
            if not result:
                result = render("templates/snippets/default_auth_button.pt",
                                {'auth_plugin': auth_plugin},
                                request = self.request)
            alternative_methods.append(result)
        self.response['alternative_methods'] = alternative_methods
        return self.register_from_method(default_auth)

    @view_config(route_name = 'register', renderer = "templates/base_edit.pt", permission  = NO_PERMISSION_REQUIRED)
    def register(self):
        browser_check_result = self.browser_check()
        if browser_check_result:
            return browser_check_result
        method_name = self.request.matchdict.get('method')
        if not method_name:
            return HTTPFound(location = self.request.resource_url(self.api.root, 'register'))
        return self.register_from_method(method_name)

    def register_from_method(self, method_name):
        auth_method = self.request.registry.getMultiAdapter((self.context, self.request), IAuthPlugin, name = method_name)
        return auth_method.render_register(self.api, self.response)

    @view_config(context=ISiteRoot, name='logout', permission = NO_PERMISSION_REQUIRED)
    def logout(self):
        headers = forget(self.request)
        return HTTPFound(location = self.request.resource_url(self.context),
                         headers = headers)
