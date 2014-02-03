from urllib import unquote

import deform
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema
from zope.interface import implementer
from zope.component import adapter
from pyramid.interfaces import IRequest
from pyramid.events import subscriber
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember

from voteit.core import VoteITMF as _
from voteit.core.interfaces import ILoginSchemaCreated
from voteit.core.interfaces import IRegisterSchemaCreated
from voteit.core.events import LoginSchemaCreated
from voteit.core.events import RegisterSchemaCreated
from voteit.core.models.interfaces import IAuthPlugin
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_login
from voteit.core.models.schemas import button_register


@adapter(ISiteRoot, IRequest)
@implementer(IAuthPlugin)
class AuthPlugin(object):
    """ Authentication base.
        See :mod:`voteit.core.models.interfaces.IAuthPlugin`.
    """
    name = u""
    title = u""
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def login_url(self):
        return self.request.resource_url(self.context, 'login', query = {'method': self.name})
    
    def register_url(self):
        return self.request.resource_url(self.context, 'register', self.name)

    def render_login_info(self):
        pass

    def render_register_info(self):
        pass

    def login(self, appstruct):
        raise NotImplementedError("Must be implemented by subclass")

    def register(self, appstruct):
        name = appstruct.pop('userid')
        obj = createContent('User', creators=[name], **appstruct)
        self.context.users[name] = obj
        return obj

    def modify_login_schema(self, schema):
        pass

    def login_appstruct(self, context, request, schema):
        return {}

    def login_form(self, schema, buttons = (button_login,), **kw):
        return deform.Form(schema, buttons=buttons, **kw)

    def create_login_schema(self, api, **kw):
        schema = createSchema('LoginSchema')
        add_csrf_token(self.context, self.request, schema)
        event = LoginSchemaCreated(schema, self)
        self.request.registry.notify(event)
        return schema.bind(context = self.context, request = self.request, api = api, **kw)

    def render_login(self, api, response):
        schema = self.create_login_schema(api)
        form = self.login_form(schema, action = self.login_url())
        POST = self.request.POST
        if 'login' in POST:
            controls = POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                response['form'] = e.render()
                return response
            return self.login(appstruct)
        response['form'] = form.render()
        return response

    def modify_register_schema(self, schema):
        pass

    def register_appstruct(self, context, request, schema):
        return {}

    def register_form(self, schema, buttons = (button_register,), **kw):
        return deform.Form(schema, buttons=buttons, **kw)

    def create_register_schema(self, api, **kw):
        schema = createSchema('RegisterSchema')
        add_csrf_token(self.context, self.request, schema)
        event = RegisterSchemaCreated(schema, self)
        self.request.registry.notify(event)
        return schema.bind(context = self.context, request = self.request, api = api, **kw)

    def render_register(self, api, response):
        schema = self.create_register_schema(api)
        form = self.register_form(schema, action = self.register_url())
        POST = self.request.POST
        if 'register' in POST:
            controls = POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                response['form'] = e.render()
                return response
            came_from = unquote(appstruct.pop('came_from'))
            if came_from == u'/':
                came_from = None
            obj = self.register(appstruct)
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
            api.flash_messages.add(msg)
            return HTTPFound(location = url, headers = headers)
        #Adjust appstruct to include any default values that might have been passed along
        appstruct = self.register_appstruct(self.context, self.request, schema)
        response['form'] = form.render(appstruct = appstruct)
        return response
        

@subscriber(ILoginSchemaCreated)
def modify_login_schema(event):
    event.method.modify_login_schema(event.schema)

@subscriber(IRegisterSchemaCreated)
def modify_register_schema(event):
    event.method.modify_register_schema(event.schema)
