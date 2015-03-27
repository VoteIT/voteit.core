import string
from random import choice
from datetime import timedelta
import logging

from BTrees.OOBTree import OOBTree
from arche.api import User as ArcheUser
from pyramid.i18n import get_localizer
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from zope.interface import implementer

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.exceptions import TokenValidationError
from voteit.core.models.base_content import BaseContent
from voteit.core.models.date_time_util import utcnow
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProfileImage
from voteit.core.models.interfaces import IUser


USERID_REGEXP = r"[a-z]{1}[a-z0-9-_]{2,30}"
log = logging.getLogger(__name__)


@implementer(IUser)
class User(ArcheUser, BaseContent):
    """ User content type.
        See :mod:`voteit.core.models.interfaces.IUser`.
        All methods are documented in the interface of this class.
    """
    type_name = 'User'
    type_title = _(u"User")
    add_permission = security.ADD_USER

    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, security.VIEW, security.CHANGE_PASSWORD, security.MANAGE_SERVER, security.DELETE)),
               (Allow, security.ROLE_OWNER, (security.EDIT, security.VIEW, security.CHANGE_PASSWORD,)),
               DENY_ALL]

    #FIXME: Review
    @property
    def auth_domains(self):
        try:
            return self.__auth_domains__
        except AttributeError:
            self.__auth_domains__ = OOBTree()
            return self.__auth_domains__

    @property
    def profile_image_plugin(self):
        #Arche compat
        return self.get_field_value('profile_image_plugin', '')
    @profile_image_plugin.setter
    def profile_image_plugin(self, value):
        self.set_field_value('profile_image_plugin', value)

    def get_image_plugin(self, request):
        name = self.get_field_value('profile_image_plugin', None)
        adapter = None
        if name:
            adapter = request.registry.queryAdapter(self, IProfileImage, name = name)
            if adapter:
                return adapter
        return request.registry.queryAdapter(self, IProfileImage, name = 'gravatar_profile_image')

    def get_image_tag(self, size = 40, request = None, **kwargs):
        if request is None:
            request = get_current_request()
        plugin = self.get_image_plugin(request)
        url = None
        if plugin:
            try:
                url = plugin.url(size, request)
            except Exception, e:
                log.error('Image plugin %s caused the exception: %s') % (plugin, e)
        if not url:
            url = request.registry.settings.get('voteit.default_profile_picture', '')
        tag = '<img src="%(url)s" height="%(size)s" width="%(size)s"' % {'url': url, 'size': size}
        for (k, v) in kwargs.items():
            tag += ' %s="%s"' % (k, v)
        if not 'class' in kwargs:
            tag += ' class="profile-pic"'
        tag += ' />'
        return tag

#     #b/c
#     def get_password(self):
#         return self.get_field_value('password')
# 
#     #b/c
#     def set_password(self, value):
#         """ Encrypt a plaintext password. Convenience method for field password for b/c."""
#         self.set_field_value('password', value)
# 
#     password = property(get_password, set_password)

    @property
    def first_name(self):
        #Arche compat
        return self.get_field_value('first_name', '')
    @first_name.setter
    def first_name(self, value):
        self.set_field_value('first_name', value)

    @property
    def last_name(self):
        #Arche compat
        return self.get_field_value('last_name', '')
    @last_name.setter
    def last_name(self, value):
        self.set_field_value('last_name', value)

    @property
    def email(self):
        #Arche compat
        return self.get_field_value('email', '')
    @email.setter
    def email(self, value):
        self.set_field_value('email', value)

    @property
    def about_me(self):
        #Arche compat
        return self.get_field_value('about_me', '')
    @about_me.setter
    def about_me(self, value):
        self.set_field_value('about_me', value)

    def send_mention_notification(self, context, request):
        """ Sends an email when the user is mentioned in a proposal or a discussion post
        """
        #FIXME: This shouldn't be part of the persistent object.
        # do not send mail if there is no emailadress
        if self.get_field_value('email'):
            locale = get_localizer(request)
            meeting = find_interface(context, IMeeting)
            agenda_item = find_interface(context, IAgendaItem)
            #FIXME: Email should use a proper template
            url = request.resource_url(context)
            link = "<a href=\"%s\">%s</a>" % (url, url)
            body = locale.translate(_('mentioned_notification',
                                      default = "You have been mentioned in ${meeting} on ${agenda_item}. "
                                        "Click the following link to go there, ${link}.",
                                        mapping = {'meeting':meeting.title,
                                                   'agenda_item': agenda_item.title,
                                                   'link': link,},))
            msg = Message(subject=_(u"You have been mentioned in VoteIT"),
                           recipients=[self.get_field_value('email')],
                           html=body)
            mailer = get_mailer(request)
            mailer.send(msg)


def includeme(config):
    config.add_content_factory(User, addable_to = ('Users',))

#@content_factory('RequestPasswordToken')

#Deprecated, clear from db
class RequestPasswordToken(object):
    """ Object that keeps track of password request tokens. """
    
    def __init__(self):
        self.token = ''.join([choice(string.letters + string.digits) for x in range(30)])
        self.created = utcnow()
        self.expires = self.created + timedelta(days=3)
        
    def __call__(self):
        return self.token
    
    def validate(self, value):
        if value != self.token:
            raise TokenValidationError("Token doesn't match.")
        if utcnow() > self.expires:
            raise TokenValidationError("Token expired.")
