import string
from random import choice
from hashlib import md5
from datetime import timedelta

from zope.interface import implements
from repoze.folder import unicodify
from pyramid.url import resource_url
from pyramid.security import Allow
from pyramid.security import DENY_ALL
from pyramid.traversal import find_interface
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.i18n import get_localizer
from betahaus.pyracont.decorators import content_factory
from betahaus.pyracont.factories import createContent
from betahaus.viewcomponent import render_view_action

from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem
from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.date_time_util import utcnow
from voteit.core.exceptions import TokenValidationError


USERID_REGEXP = r"[a-zA-Z]{1}[\w-]{2,14}"


@content_factory('User', title=_(u"User"))
class User(BaseContent):
    """ User content type.
        See :mod:`voteit.core.models.interfaces.IUser`.
        All methods are documented in the interface of this class.
    """
    implements(IUser, ICatalogMetadataEnabled)
    content_type = 'User'
    display_name = _(u"User")
    allowed_contexts = ('Users',)
    add_permission = security.ADD_USER
    custom_mutators = {'title':'_set_title'}
    custom_fields = {'password':'PasswordField'}
    schemas = {'add': 'AddUserSchema', 'edit': 'EditUserSchema'}

    __acl__ = [(Allow, security.ROLE_ADMIN, (security.EDIT, security.VIEW, security.CHANGE_PASSWORD, security.MANAGE_SERVER, )),
               (Allow, security.ROLE_OWNER, (security.EDIT, security.VIEW, security.CHANGE_PASSWORD,)),
               DENY_ALL]
    
    @property
    def userid(self):
        """ Convention - name should always be same as userid """
        return self.__name__
    
    def get_image_tag(self, size=40, **kwargs):
        """ Get image tag. Always square, so size is enough.
            Other keyword args will be converted to html properties.
            Appends class 'profile-pic' to tag if class isn't part of keywords.
        """
        
        email_hash = self.get_field_value('email_hash', None)
        tag = '<img src="http://www.gravatar.com/avatar/'
        if email_hash:
            tag += email_hash
        tag += '?d=mm&s=%(size)s" height="%(size)s" width="%(size)s"' % {'size':size}
        
        for (k, v) in kwargs.items():
            tag += ' %s="%s"' % (k, v)
        if not 'class' in kwargs:
            tag += ' class="profile-pic"'
        tag += ' />'
        
        return tag

    def get_password(self):
        return self.get_field_value('password')
    
    def set_password(self, value):
        """ Encrypt a plaintext password. Convenience method for field password for b/c."""
        self.set_field_value('password', value)

    #Override title for users
    def _set_title(self, value, key=None):
        #Not used for user content type
        pass
    
    def _get_title(self):
        out = "%s %s" % ( self.get_field_value('first_name', ''), self.get_field_value('last_name', '') )
        return out.strip()

    title = property(_get_title, _set_title)

    def new_request_password_token(self, request):
        """ Set a new request password token and email user. """
        locale = get_localizer(request)
        self.__token__ = createContent('RequestPasswordToken')
        pw_link = "%stoken_pw?token=%s" % (resource_url(self, request), self.__token__())
        html = render_view_action(self, request, 'email', 'request_password',
                                  pw_link = pw_link)
        msg = Message(subject=_(u"Password reset request from VoteIT"),
                      recipients=[self.get_field_value('email')],
                      html = html)
        mailer = get_mailer(request)
        mailer.send(msg)
        
    def remove_password_token(self):
        self.__token__ = None

    def get_token(self):
        """ Get password token, or None. """
        return getattr(self, '__token__', None)

    def generate_email_hash(self):
        """ Save an md5 hash of an email address.
            Used to generate urls for gravatar profile images.
        """
        email = self.get_field_value('email', '').strip().lower()
        if email:
            self.set_field_value('email_hash', md5(email).hexdigest())
            
    def send_mention_notification(self, context, request):
        """ Sends an email when the user is mentioned in a proposal or a discussion post
        """
        
        # do not send mail if there is no emailadress
        if self.get_field_value('email'):
            locale = get_localizer(request)
            
            meeting = find_interface(context, IMeeting)
            agenda_item = find_interface(context, IAgendaItem)
            
            #FIXME: Email should use a proper template
            url = resource_url(context, request)
            link = "<a href=\"%s\">%s</a>" % (url, url)
            body = locale.translate(_('mentioned_notification',
                     default=u"You have been mentioned in ${meeting} on ${agenda_item}. Click the following link to go there, ${link}.",
                     mapping={'meeting':meeting.title, 'agenda_item': agenda_item.title, 'link': link,},))
            
            msg = Message(subject=_(u"You have been mentioned in VoteIT"),
                           recipients=[self.get_field_value('email')],
                           html=body)

            mailer = get_mailer(request)
            mailer.send(msg)


@content_factory('RequestPasswordToken')
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
