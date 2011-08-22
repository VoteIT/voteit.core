from pyramid.view import view_config
import colander
import urllib
from deform import Form
from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.url import resource_url
from pyramid.security import remember
from pyramid.security import forget

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IContentUtility
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers
from voteit.core.views.api import APIView
from voteit.core.security import CHANGE_PASSWORD, ROLE_OWNER
from voteit.core.models.schemas import add_csrf_token, button_add, button_cancel,\
    button_update, button_change, button_login, button_register, button_request
from voteit.core.models.user import get_sha_password


DEFAULT_TEMPLATE = "templates/base_edit.pt"
LOGIN_REGISTER_TPL = "templates/login_register.pt"

class UsersView(object):
    """ View class for adding, editing or deleting users.
        It also handles users own login and registration.
    """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = self.api = APIView(context, request)

    @view_config(context=IUsers, name="add", renderer=DEFAULT_TEMPLATE)
    def add_form(self):
        #FIXME: Utility might need to handle different schemas here?
        content_util = self.request.registry.getUtility(IContentUtility)
        schema = content_util['User'].schema(context=self.context, request=self.request, type='add')
        add_csrf_token(self.context, self.request, schema)

        self.form = Form(schema, buttons=(button_add, button_cancel))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'add' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = self.form.validate(controls)
                #FIXME: validate name - it must be unique and url-id-like
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            obj = content_util['User'].type_class()
            
            if appstruct['password']:
                #At this point the validation should have been done
                obj.set_password(appstruct['password'])
                
            #Remove the field since it's handled - to avoid blanking the already set password
            if 'password' in appstruct:
                del appstruct['password']
            
            #Userid and name should be consistent
            name = appstruct['userid']
            del appstruct['userid']
            
            obj.set_field_appstruct(appstruct)

            #The user should be owner of the user object
            obj.add_groups(name, (ROLE_OWNER,))

            #self.context is the site root. Users are stored in the users-property
            self.context[name] = obj

            self.api.flash_messages.add(_(u"Successfully added"))

            url = resource_url(self.context, self.request)            
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render add form
        msg = _(u"Add new user")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = self.form.render()
        return self.response

    @view_config(context=IUsers, name="list", renderer='templates/list_users.pt')
    def list_users(self):
        return self.response

    @view_config(context=IUser, renderer='templates/view_user.pt')
    def view_users(self):
        return self.response

    @view_config(context=IUser, name="change_password", renderer=DEFAULT_TEMPLATE, permission=CHANGE_PASSWORD)
    def password_form(self):
        content_util = self.request.registry.getUtility(IContentUtility)
        schema = content_util['User'].schema(context=self.context, request=self.request, type='change_password')
        add_csrf_token(self.context, self.request, schema)

        self.form = Form(schema, buttons=(button_update, button_cancel))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'update' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = self.form.validate(controls)
                #FIXME: validate name - it must be unique and url-id-like
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            self.context.set_password(appstruct['password'])
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response

    @view_config(context=IUser, name="token_pw", renderer=DEFAULT_TEMPLATE)
    def token_password_change(self):
        content_util = self.request.registry.getUtility(IContentUtility)
        schema = content_util['User'].schema(context=self.context, request=self.request, type='token_password_change')

        self.form = Form(schema, buttons=(button_change, button_cancel))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'change' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = self.form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            self.context.set_password(appstruct['password'])
            self.api.flash_messages.add(_(u"Password set. You may login now."))
            url = "%s@@login" % resource_url(self.api.root, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.api.root, self.request)
            return HTTPFound(location=url)

        #Fetch token from get request
        token = self.request.GET.get('token', None)
        if token is None:
            msg = _(u"Invalid security token. Did you click the link in your email?")
            self.api.flash_messages.add(msg, type="error")
            url = resource_url(self.api.root, self.request)
            return HTTPFound(location=url)

        #Everything seems okay. Render form
        appstruct = dict(token = token)
        self.response['form'] = self.form.render(appstruct=appstruct)
        return self.response

    @view_config(context=ISiteRoot, name="register", renderer=LOGIN_REGISTER_TPL)
    @view_config(context=ISiteRoot, name='login', renderer=LOGIN_REGISTER_TPL)
    def login_or_register(self):
        content_util = self.request.registry.getUtility(IContentUtility)
        users = self.api.root.users
        
        login_schema = content_util['User'].schema(context=self.context, request=self.request, type='login')
        register_schema = content_util['User'].schema(context=users, request=self.request, type='registration')

        login_form = Form(login_schema, buttons=(button_login,))
        reg_form = Form(register_schema, buttons=(button_register,))

        #Join form resources
        form_resources = login_form.get_widget_resources()
        for (k, v) in reg_form.get_widget_resources().items():
            if k in form_resources:
                form_resources[k].extend(v)
            else:
                form_resources[k] = v
        
        self.response['form_resources'] = form_resources

        
        POST = self.request.POST
    
        #Handle submitted information
        if 'login' in POST:
            controls = POST.items()
    
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = login_form.validate(controls)
            except ValidationFailure, e:
                self.response['login_form'] = e.render()
                return self.response
            
            userid = appstruct['userid']
            password = appstruct['password']
            came_from = urllib.unquote(appstruct['came_from'])
    
            #userid here can be either an email address or a login name
            if '@' in userid:
                #assume email
                user = users.get_user_by_email(userid)
            else:
                user = users.get(userid)
            
            if IUser.providedBy(user):
                if get_sha_password(password) == user.get_password():
                    headers = remember(self.request, user.__name__)
                    url = resource_url(self.context, self.request)
                    if came_from:
                        url = came_from
                    return HTTPFound(location = url,
                                     headers = headers)
            self.response['api'].flash_messages.add(_('Login failed.'), type='error')


        if 'register' in POST:
            controls = POST.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = reg_form.validate(controls)
                #FIXME: validate name - it must be unique and url-id-like
            except ValidationFailure, e:
                self.response['reg_form'] = e.render()
                return self.response
            
            obj = content_util['User'].type_class()
            
            obj.set_password(appstruct['password'])
                
            #Remove the field since it's handled - to avoid blanking the already set password
            if 'password' in appstruct:
                del appstruct['password']
            
            #Userid and name should be consistent
            name = appstruct['userid']
            del appstruct['userid']
            
            for (k, v) in appstruct.items():
                obj.set_field_value(k, v)

            #The user should be owner of the user object
            obj.add_groups(name, (ROLE_OWNER,))

            #self.context is the site root. Users are stored in the users-property
            users[name] = obj

            #FIXME: Validate email address instead!
            url = "%slogin" % resource_url(self.context, self.request)

            headers = remember(self.request, name)  # login user

            came_from = urllib.unquote(appstruct['came_from'])
            if came_from:
                url = came_from
            return HTTPFound(location=url, headers=headers)

        #Render forms
        self.response['login_form'] = login_form.render()
        self.response['reg_form'] = reg_form.render()
        return self.response


    @view_config(context=ISiteRoot, name='request_password',
                 renderer='templates/base_edit.pt')
    def request_password(self):
        content_util = self.request.registry.getUtility(IContentUtility)
        
        schema = content_util['User'].schema(context=self.context, request=self.request, type='request_password')
        form = Form(schema, buttons=(button_request, button_cancel))
        response['form_resources'] = form.get_widget_resources()
    
        #Handle submitted information
        if 'request' in self.request.POST:
            controls = self.request.POST.items()
    
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
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
                url = resource_url(self.api.root, self.request)
                return HTTPFound(location = url)
    
            self.api.flash_messages.add(_('Username or email not found.'), type='error')
        
        if 'cancel' in self.request.POST:
            url = resource_url(self.api.root, self.request)
            return HTTPFound(location = url)
    
        #Render form
        self.response['form'] = form.render()
        return self.response
        
        
    @view_config(context=ISiteRoot, name='logout')
    def logout(self):
        headers = forget(self.request)
        return HTTPFound(location = resource_url(self.context, self.request),
                         headers = headers)
