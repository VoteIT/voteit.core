import urllib

import deform
import httpagentparser
from decimal import Decimal
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.security import remember
from pyramid.security import forget
from pyramid.renderers import render
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core.helpers import ajax_options
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_save
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_login
from voteit.core.models.schemas import button_register
from voteit.core.views.base_edit import BaseEdit
from voteit.core import VoteITMF as _


class SiteFormView(BaseEdit):

    @view_config(context=ISiteRoot, name="register", renderer="templates/login_register.pt")
    @view_config(context=ISiteRoot, name='login', renderer="templates/login_register.pt")
    def login_or_register(self):
        #Browser check
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
        
        users = self.api.root.users
        
        login_schema = createSchema('LoginSchema').bind(context=self.context, request=self.request, api=self.api)        
        register_schema = createSchema('RegisterUserSchema').bind(context=self.context, request=self.request, api=self.api)

        login_form = deform.Form(login_schema, buttons=(button_login,))
        reg_form = deform.Form(register_schema, buttons=(button_register,))

        self.api.register_form_resources(login_form)
        self.api.register_form_resources(reg_form)

        appstruct = {}

        POST = self.request.POST
    
        #Handle submitted information
        if 'login' in POST:
            controls = POST.items()
    
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = login_form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['login_form'] = e.render()
                return self.response
            
            # Forece lowercase userid
            userid = appstruct['userid'].lower()
            password = appstruct['password']
            came_from = appstruct['came_from']
    
            #userid here can be either an email address or a login name
            if '@' in userid:
                #assume email
                user = users.get_user_by_email(userid)
            else:
                user = users.get(userid)
            
            if IUser.providedBy(user):
                pw_field = user.get_custom_field('password')
                if pw_field.check_input(password):
                    headers = remember(self.request, user.__name__)
                    url = self.request.resource_url(self.context)
                    if came_from:
                        url = urllib.unquote(came_from)
                    return HTTPFound(location = url,
                                     headers = headers)
            self.response['api'].flash_messages.add(_('Login failed.'), type='error')

        if 'register' in POST:
            controls = POST.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = reg_form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['reg_form'] = e.render()
                return self.response
            
            #Userid and name should be consistent - and not stored
            name = appstruct['userid']
            del appstruct['userid']

            #Came from should not be stored either
            came_from = urllib.unquote(appstruct['came_from'])
            if came_from:
                url = came_from
            else:
                url = self.request.resource_url(self.context, 'login')
            del appstruct['came_from']

            obj = createContent('User', creators=[name], **appstruct)
            self.context.users[name] = obj
            headers = remember(self.request, name)  # login user

            return HTTPFound(location=url, headers=headers)

        #Set came from in form
        came_from = self.request.GET.get('came_from', None)
        if came_from:
            appstruct['came_from'] = came_from

        #Render forms
        self.response['login_form'] = login_form.render(appstruct)
        self.response['reg_form'] = reg_form.render(appstruct)
        return self.response

    @view_config(context=ISiteRoot, name='logout')
    def logout(self):
        headers = forget(self.request)
        return HTTPFound(location = self.request.resource_url(self.context),
                         headers = headers)

    @view_config(name="recaptcha", context=ISiteRoot, renderer="templates/base_edit.pt", permission = security.EDIT)
    def recaptcha(self):
        schema = createSchema("CaptchaSiteRootSchema").bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)
        form = deform.Form(schema, buttons=(button_save, button_cancel), use_ajax=True, ajax_options=ajax_options)
        self.api.register_form_resources(form)

        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                if self.request.is_xhr:
                    return Response(render("templates/ajax_edit.pt", self.response, request = self.request))
                
                return self.response
            
            self.context.set_field_appstruct(appstruct)
            
            url = self.request.resource_url(self.context)
            if self.request.is_xhr:
                return Response(headers = [('X-Relocate', url)])
            return HTTPFound(location=url)

        #FIXME: with ajax post this does not work no, we'll need to fix this
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))

            url = self.request.resource_url(self.context)
            if self.request.is_xhr:
                return Response(headers = [('X-Relocate', url)])
            return HTTPFound(location=url)

        #No action - Render form
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = form.render(appstruct)
        return self.response
