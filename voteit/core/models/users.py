from zope.interface import implements
from pyramid.security import Allow
from pyramid.security import DENY_ALL

from voteit.core import VoteITMF as _
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers
from voteit.core import security
from betahaus.pyracont.decorators import content_factory

from voteit.core.validators import NEW_USERID_PATTERN


@content_factory('Users', title=_(u"Users"))
class Users(BaseContent):
    """ Container for all user objects """
    implements(IUsers)
    content_type = 'Users'
    display_name = _(u"Users")
    allowed_contexts = ()
    add_permission = None

    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, security.VIEW, security.ADD_USER, security.MANAGE_SERVER)),
               DENY_ALL]
    
    def add(self, name, *args, **kvargs):
        if not NEW_USERID_PATTERN.match(name):
            raise ValueError('name must start with lowercase a-z and only contain lowercase a-z, numbers, minus and underscore')

        super(Users, self).add(name, *args, **kvargs)

    def get_user_by_email(self, email):
        for user in self.get_content(iface=IUser):
            if user.get_field_value('email') == email:
                return user
                
    def get_user_by_oauth_token(self, token):
        for user in self.get_content(iface=IUser):
            if user.get_field_value('oauthAccessToken') == token:
                return user
