from betahaus.pyracont.factories import createContent
from zope.interface import implementer
from zope.component import adapter
from pyramid.interfaces import IRequest
from pyramid.events import subscriber

from voteit.core import VoteITMF as _
from voteit.core.interfaces import ILoginSchemaCreated
from voteit.core.interfaces import IRegisterSchemaCreated
from voteit.core.models.interfaces import IAuthPlugin
from voteit.core.models.interfaces import ISiteRoot


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

    def modify_register_schema(self, schema):
        pass

    def register_appstruct(self, context, request, schema):
        return {}

@subscriber(ILoginSchemaCreated)
def modify_login_schema(event):
    event.method.modify_login_schema(event.schema)

@subscriber(IRegisterSchemaCreated)
def modify_register_schema(event):
    event.method.modify_register_schema(event.schema)
