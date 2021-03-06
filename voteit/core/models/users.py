from __future__ import unicode_literals

from arche.api import Users as ArcheUsers
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from zope.interface import implementer

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUsers


@implementer(IUsers)
class Users(BaseContent, ArcheUsers):
    """ Container for all user objects """
    type_name = 'Users'
    type_title = title = _("Users")
    nav_visible = False

    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, security.VIEW, security.ADD_USER, security.MANAGE_SERVER, security.PERM_MANAGE_USERS)),
               DENY_ALL]

#     def add(self, name, *args, **kvargs):
#         if not NEW_USERID_PATTERN.match(name):
#             raise ValueError('name must start with lowercase a-z and only contain lowercase a-z, numbers, minus and underscore')
#  
#         super(Users, self).add(name, *args, **kvargs)

        #Arche has this, check compat
#     def get_user_by_email(self, email):
#         for user in self.get_content(iface=IUser):
#             if user.get_field_value('email') == email:
#                 return user

#     def get_auth_domain_user(self, domain, key, value):
#         for user in self.get_content(iface=IUser):
#             if domain in user.auth_domains and user.auth_domains[domain][key] == value:
#                 return user
# 
#     def get_user_by_oauth_token(self, domain, token):
#         #b / c compat - remove
#         return self.get_auth_domain_user(domain, 'oauth_access_token', token)

def includeme(config):
    config.add_content_factory(Users, addable_in = ('User',))
