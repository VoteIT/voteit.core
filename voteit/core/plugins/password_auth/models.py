import string
from random import choice
from datetime import timedelta

import colander
import deform
from zope.interface import implementer
from zope.component import adapter
from pyramid.renderers import render
from pyramid.security import remember
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_localizer
from pyramid_mailer.message import Message
from pyramid_mailer import get_mailer
from betahaus.pyracont.decorators import content_factory
from betahaus.pyracont.factories import createContent
from betahaus.viewcomponent import render_view_action

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IUser
from voteit.core.models.auth import AuthPlugin
from voteit.core.models.date_time_util import utcnow
from .schemas import password_node
from .schemas import deferred_login_password_validator
from .interfaces import IPasswordHandler


class PasswordAuth(AuthPlugin):
    name = u"password"

    def modify_login_schema(self, schema):
        schema.add(colander.SchemaNode(colander.String(),
                                       name = "password",
                                       title = _('Password'),
                                       widget = deform.widget.PasswordWidget(size=20)))
        schema.validator = deferred_login_password_validator

    def modify_register_schema(self, schema):
        pw_node = password_node()
        pw_node.name = u"password"
        schema.add(pw_node)

    def login(self, appstruct):
        userid = appstruct['userid']
        assert 'password' in appstruct #Just to make sure, but it has already been validated.
        headers = remember(self.request, userid)
        url = appstruct.get('url', self.request.resource_url(self.context))
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
        pw_link = request.resource_url(self.context, 'token_pw', query = {'token': token()})
        response = {'pw_link': pw_link,
                    'context': self.context}
        html = render('request_password_email.pt', response, request = request)
        msg = Message(subject = _(u"Password reset request from VoteIT"),
                      recipients = [self.context.get_field_value('email')],
                      html = html)
        mailer = get_mailer(request)
        mailer.send(msg)
        
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
