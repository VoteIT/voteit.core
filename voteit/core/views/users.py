from pyramid.view import view_config
import colander
from deform import Form
from deform.exception import ValidationFailure
from webob.exc import HTTPFound
from pyramid.url import resource_url

from voteit.core.models.user import AddUserSchema, User, EditUserSchema,\
    ChangePasswordSchema
from voteit.core.models.users import Users
from voteit.core.views.api import APIView
from voteit.core.models.site import SiteRoot

DEFAULT_TEMPLATE = "templates/base_edit.pt"


class UsersView(object):
    """ View class for adding, editing or deleting users. """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = APIView(context, request)

    @view_config(context=Users, name="add", renderer=DEFAULT_TEMPLATE)
    def add_form(self):
        schema = AddUserSchema()

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
            
            obj = User()
            
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
            self.context[name] = obj
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response

    @view_config(context=SiteRoot, name="register", renderer=DEFAULT_TEMPLATE)
    def registration_form(self):
        schema = AddUserSchema()

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
            
            obj = User()
            
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
            self.context.users[name] = obj
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response

    @view_config(context=Users, name="list", renderer='templates/list_users.pt')
    def list_users(self):
        return self.response

    @view_config(context=User, name="edit", renderer=DEFAULT_TEMPLATE)
    def edit_form(self):
        schema = EditUserSchema()
        
        #Make the current value the default value
        for field in schema:
            field.default = self.context.get_field_value(field.name)

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
            
            for (k, v) in appstruct.items():
                self.context.set_field_value(k, v)
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response

    @view_config(context=User, name="change_password", renderer=DEFAULT_TEMPLATE)
    def password_form(self):
        schema = ChangePasswordSchema()

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