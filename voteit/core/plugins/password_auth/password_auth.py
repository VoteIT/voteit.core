import string
from random import choice
from datetime import timedelta

import colander
import deform
from betahaus.pyracont.decorators import content_factory
from betahaus.pyracont.decorators import schema_factory
from pyramid.traversal import find_root
from pyramid.security import remember
from pyramid.httpexceptions import HTTPFound

from voteit.core.models.auth import AuthPlugin
from voteit.core.validators import html_string_validator
from voteit.core.models.interfaces import ISiteRoot
from voteit.core import VoteITMF as _
from voteit.core.models.date_time_util import utcnow


@content_factory('RequestPasswordToken')
class RequestPasswordToken(object):
    """ Object that keeps track of password request tokens. """
     
    def __init__(self):
        self.token = ''.join([choice(string.letters + string.digits) for x in range(30)])
        self.created = utcnow()
        self.expires = self.created + timedelta(days=3)
         
    def __call__(self):
        return self.token
     
    def validate(self, node, value):
        if not self.token or value != self.token:
            raise colander.Invalid(node, _(u"Token doesn't match."))
        if utcnow() > self.expires:
            raise colander.Invalid(node, _("Token expired."))
