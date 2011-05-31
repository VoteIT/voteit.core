from pyramid.view import view_config
import colander
from deform import Form
from deform.exception import ValidationFailure
from webob.exc import HTTPFound
from pyramid.url import resource_url

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IContentUtility
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers
from voteit.core.views.api import APIView
from voteit.core.security import CHANGE_PASSWORD, ROLE_OWNER
from voteit.core.models.schemas import add_csrf_token

DEFAULT_TEMPLATE = "templates/base_edit.pt"


class UsersView(object):
    """ View class for adding, editing or deleting users. """
        
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

        self.form = Form(schema, buttons=('add', 'cancel'))
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

    @view_config(context=ISiteRoot, name="register", renderer=DEFAULT_TEMPLATE)
    def registration_form(self):
        users = self.context.users
        content_util = self.request.registry.getUtility(IContentUtility)
        schema = content_util['User'].schema(context=users, request=self.request, type='registration')
        add_csrf_token(self.context, self.request, schema)

        self.form = Form(schema, buttons=('register', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'register' in post:
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
            
            for (k, v) in appstruct.items():
                obj.set_field_value(k, v)
            
            #self.context is the site root. Users are stored in the users-property
            users[name] = obj

            self.api.flash_messages.add(_(u"Successfully registered - you may now log in!"))
            url = "%slogin" % resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render registration form
        msg = _(u"New user registration")
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

        self.form = Form(schema, buttons=('update', 'cancel'))
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

        self.form = Form(schema, buttons=('change', 'cancel'))
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
