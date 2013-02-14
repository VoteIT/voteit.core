import urllib

import deform
import httpagentparser
from decimal import Decimal
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
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
from voteit.core.validators import deferred_login_password_validator


class SiteFormView(BaseEdit):

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

    @view_config(context=ISiteRoot, name='login', renderer = 'templates/base_edit.pt')
    def login(self):
        """ Login action used by sidebar widget for password login. """
        browser_result = self.browser_check()
        if browser_result:
            return browser_result
        #FIXME: Validation in schema, not in view
        schema = createSchema('LoginSchema', validator = deferred_login_password_validator).bind(context=self.context, request=self.request, api=self.api)
        form = deform.Form(schema, buttons=(button_login,))
        self.api.register_form_resources(form)
        users = self.context.users
        POST = self.request.POST
        if 'login' in POST:
            controls = POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            # Force lowercase userid
            userid = appstruct['userid'].lower()
            password = appstruct['password']
            came_from = appstruct['came_from']
            #userid here can be either an email address or a login name
            if '@' in userid:
                #assume email
                user = users.get_user_by_email(userid)
            else:
                user = users.get(userid)
            if not IUser.providedBy(user):
                raise HTTPForbidden(u"Userid returned something else then a user from users folder.")
            #Password validation already handled by schema here
            headers = remember(self.request, user.__name__)
            url = self.request.resource_url(self.context)
            if came_from:
                url = urllib.unquote(came_from)
            return HTTPFound(location = url,
                             headers = headers)
        #This view should not really be rendered, but in case someone accesses it directly
        self.response['form'] = form.render()
        return self.response

    @view_config(context=ISiteRoot, name="register", renderer="templates/register.pt")
    def register(self):
        """ Register and log in a user. Be sure to catch came_from since ticket system will use that url
            to send people who've been invited but haven't registered yet to this view.
        """
        browser_result = self.browser_check()
        if browser_result:
            return browser_result
        schema = createSchema('RegisterUserSchema').bind(context=self.context, request=self.request, api=self.api)
        form = deform.Form(schema, buttons=(button_register,))
        self.api.register_form_resources(form)
        appstruct = {}

        POST = self.request.POST
        users = self.context.users

        if 'register' in POST:
            controls = POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            #Userid and name should be consistent - and not stored
            name = appstruct['userid']
            del appstruct['userid']
            #Came from should not be stored either
            came_from = urllib.unquote(appstruct['came_from'])
            if came_from == u'/':
                came_from = None
            del appstruct['came_from']
            obj = createContent('User', creators=[name], **appstruct)
            self.context.users[name] = obj
            headers = remember(self.request, name)  # login user
            if came_from:
                msg = _(u"You're now registered. Welcome!")
                self.api.flash_messages.add(msg)
                return HTTPFound(location=came_from, headers=headers)
            msg = _(u"joined_without_ticket_intro_text",
                    default = u"You're now registered. Welcome! "
                              u"Please take some time to update your profile and write something about yourself. "
                              u"To join a meeting, you need to either have an invitaion that will have been sent "
                              u"to you via email, or the url of a meeting to request access to it.")
            self.api.flash_messages.add(msg)
            return HTTPFound(location=self.request.resource_url(obj), headers=headers)

        #Set came from in form
        came_from = self.request.GET.get('came_from', None)
        if came_from:
            appstruct['came_from'] = came_from
        #Render forms
        self.response['form'] = form.render(appstruct)
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
