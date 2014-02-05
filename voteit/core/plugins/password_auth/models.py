import string
from random import choice
from datetime import timedelta

import colander
import deform
from zope.interface import implementer
from zope.component import adapter
from pyramid.security import remember
from pyramid.httpexceptions import HTTPFound
from betahaus.viewcomponent import render_view_action

from voteit.core import VoteITMF as _
from voteit.core.helpers import send_email
from voteit.core.models.interfaces import IUser
from voteit.core.models.auth import AuthPlugin
from voteit.core.models.date_time_util import utcnow
from voteit.core.models.schemas import button_login
from .schemas import password_node
from .schemas import deferred_login_password_validator
from .interfaces import IPasswordHandler


class PasswordAuth(AuthPlugin):
    name = u"password"
    title = _(u"Password")

    def modify_login_schema(self, schema):
        schema.add(colander.SchemaNode(colander.String(),
                                       name = "password",
                                       title = _('Password'),
                                       widget = deform.widget.PasswordWidget(size=20)))
        schema.validator = deferred_login_password_validator

    def render_login(self, api, response):
        schema = self.create_login_schema(api)
        form = self.login_form(schema, buttons = (button_login, deform.Button('forgot', _(u"Forgot password?"))), action = self.login_url())
        POST = self.request.POST
        if 'login' in POST:
            controls = POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                response['form'] = e.render()
                return response
            return self.login(appstruct)
        if 'forgot' in POST:
            return HTTPFound(location = self.request.resource_url(api.root, 'request_password'))
        response['form'] = form.render()
        return response

    def modify_register_schema(self, schema):
        pw_node = password_node()
        pw_node.name = u"password"
        schema.add(pw_node)

    def login(self, appstruct):
        userid = appstruct['userid']
        assert 'password' in appstruct #Just to make sure, but it has already been validated.
        headers = remember(self.request, userid)
        url = appstruct.get('came_from', None)
        if url is None:
            url = self.request.resource_url(self.context)
        return HTTPFound(location = url,
                         headers = headers)


@implementer(IPasswordHandler)
@adapter(IUser)
class PasswordHandler(object):
    """ See .interfaces.IPasswordHandler """

    def __init__(self, context):
        self.context = context

    def new_pw_token(self, request):
        self.context.__pw_request_token__ = token = RequestPasswordToken()
        html = render_view_action(self.context, request, 'email', 'request_password', token = token())
        send_email(_(u"Password reset request from VoteIT"),
                   self.context.get_field_value('email'),
                   html,
                   request = request)

    def remove_password_token(self):
        if hasattr(self, '__pw_request_token__'):
            delattr(self, '__pw_request_token__')

    def token_validator(self, node, value):
        token = self.get_token()
        if not token or value != token():
            raise colander.Invalid(node, _(u"Token doesn't match."))
        if  utcnow() > token.expires:
            raise colander.Invalid(node, _(u"Token expired."))

    def get_token(self):
        return getattr(self.context, '__pw_request_token__', None)


class RequestPasswordToken(object):
    """ Object that keeps track of password request tokens. """
     
    def __init__(self):
        self.token = ''.join([choice(string.letters + string.digits) for x in range(30)])
        self.created = utcnow()
        self.expires = self.created + timedelta(days=3)
         
    def __call__(self):
        return self.token
