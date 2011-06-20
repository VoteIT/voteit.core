from pyramid.request import Request
from pyramid.decorator import reify
from pyramid.security import authenticated_userid
from pyramid.traversal import find_interface

from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers


class VoteITRequestMixin(object):
    """ Custom request object for VoteIT.
        Contains extended and cached properties.
    """
    
    @reify
    def sql_session(self):
        session_fact = self.registry.settings.get('rdb_session_factory', None)
        if session_fact is None:
            raise ValueError("rdb_session_factory needed, shouldn't be None")
        
        return session_fact()
    
    @reify
    def userid(self):
        return authenticated_userid(self)

    @reify
    def site_root(self):
        return find_interface(self.context, ISiteRoot)

    @reify
    def users(self):
        return self.site_root.users
        
    @reify
    def user(self):
        user = self.users.get(self.userid)
        if IUser.providedBy(user):
            return user


class VoteITRequestFactory(Request, VoteITRequestMixin):
    """ Custom request factory.
    """