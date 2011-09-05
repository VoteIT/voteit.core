import re
import string
from random import choice
from hashlib import sha1
from hashlib import md5
from datetime import timedelta
import urllib

from BTrees.OOBTree import OOBTree
import colander
import deform
from zope.component import getUtility
from zope.interface import implements
from repoze.folder import unicodify
from pyramid.url import resource_url
from pyramid.security import Allow
from pyramid.traversal import find_interface
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.i18n import get_localizer

from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers
from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.validators import password_validation
from voteit.core.validators import html_string_validator
from voteit.core.models.date_time_util import utcnow


def get_sha_password(password):
    """ Encode a plaintext password to sha1. """
    if isinstance(password, unicode):
        password = password.encode('UTF-8')
    return 'SHA1:' + sha1(password).hexdigest()


class User(BaseContent):
    """ Content type for a user. Usable as a profile page. """
    implements(IUser, ICatalogMetadataEnabled)
    content_type = 'User'
    display_name = _(u"User")
    allowed_contexts = ('Users',)
    add_permission = security.ADD_USER
    
    __acl__ = [(Allow, security.ROLE_ADMIN, security.EDIT),
               (Allow, security.ROLE_OWNER, [security.EDIT, security.CHANGE_PASSWORD])]
    
    @property
    def userid(self):
        """ Convention - name should always be same as userid """
        return self.__name__
    
    def get_image_tag(self, size=40):
        email_hash = self.get_field_value('email_hash', None)
        tag = '<img src="http://www.gravatar.com/avatar/'
        if email_hash:
            tag += email_hash
        tag += '?d=mm&s=%(size)s" height="%(size)s" width="%(size)s" />' % {'size':size}
        return tag

    def get_password(self):
        return self.get_field_value('password')
    
    def set_password(self, value):
        """ Encrypt a plaintext password. """
        if not isinstance(value, unicode):
            value = unicodify(value)
        if len(value) < 5:
            raise ValueError("Password must be longer than 4 chars")
        value = get_sha_password(value)
        self.set_field_value('password', value)

    #Override title for users
    def _set_title(self, value):
        #Not used for user content type
        pass
    
    def _get_title(self):
        out = "%s %s" % ( self.get_field_value('first_name'), self.get_field_value('last_name') )
        return out.strip()

    title = property(_get_title, _set_title)

    def new_request_password_token(self, request):
        """ Set a new request password token and email user. """
        locale = get_localizer(request)
        
        #FIXME email user
        self.__token__ = RequestPasswordToken()
        
        #FIXME: Email should use a proper template
        pw_link = "%stoken_pw?token=%s" % (resource_url(self, request), self.__token__())
        body = locale.translate(_('request_new_password_text',
                 default=u"password link: ${pw_link}",
                 mapping={'pw_link':pw_link},))
        
        msg = Message(subject=_(u"Password reset request from VoteIT"),
                       recipients=[self.get_field_value('email')],
                       body=body)

        mailer = get_mailer(request)
        mailer.send(msg)
        
    def remove_password_token(self):
        self.__token__ = None

    def validate_password_token(self, node, value):
        """ Validate input from a colander form. See token_password_change schema """
        #FIXME: We need to handle an error here in a nicer way
        self.__token__.validate(value)

    def generate_email_hash(self):
        """ Save an md5 hash of an email address.
            Used to generate urls for gravatar profile images.
        """
        email = self.get_field_value('email', '').strip().lower()
        if email:
            self.set_field_value('email_hash', md5(email).hexdigest())


class RequestPasswordToken(object):
    
    def __init__(self):
        self.token = ''.join([choice(string.letters + string.digits) for x in range(30)])
        self.created = utcnow()
        self.expires = self.created + timedelta(days=3)
        
    def __call__(self):
        return self.token
    
    def validate(self, value):
        if value != self.token:
            raise ValueError("Token doesn't match.")
        if utcnow() > self.expires:
            raise ValueError("Token expired.")
        

def construct_schema(**kwargs):
    context = kwargs.get('context', None)
    request = kwargs.get('request', None)
    referer = urllib.quote(request.GET.get('came_from', '/'))
    type = kwargs.get('type', None)
    if context is None:
        KeyError("'context' is a required keyword for User schemas. See construct_schema in the user module.")    
    if type is None:
        KeyError("'type' is a required keyword for User schemas. See construct_schema in the user module.")    
        
    def _validate_email(node, value):
        default_email_validator = colander.Email(msg=_(u"Invalid email address."))
        default_email_validator(node, value)
        
        #context can be IUser or IUsers
        users = find_interface(context, IUsers)
        
        #User with email exists?
        match = users.get_user_by_email(value)
        if match and context != match:
            #Something was found, and it isn't this context - I.e. some other user
            raise colander.Invalid(node, 
                                   u"Another user has already registered with that email address. "
                                   "If you've lost your password, request a new one instead.")

    #Common schema nodes
    password_node = colander.SchemaNode(
                        colander.String(),
                        validator=colander.All(password_validation, html_string_validator,),
                        widget=deform.widget.CheckedPasswordWidget(size=20),
                        title=_('Password'))
    email_node = colander.SchemaNode(colander.String(),
                                     title=_(u"Email"),
                                     validator=colander.All(_validate_email, html_string_validator,),)
    first_name_node = colander.SchemaNode(colander.String(),
                                          title=_(u"First name"),
                                          validator=html_string_validator,)
    last_name_node = colander.SchemaNode(colander.String(),
                                         title=_(u"Last name"),
                                         missing=u"",
                                         validator=html_string_validator,)


    came_from_node = colander.SchemaNode(colander.String(),
                                         widget = deform.widget.HiddenWidget(),
                                         default=referer,)

    if type == 'login':
        class LoginSchema(colander.Schema):
            userid = colander.SchemaNode(colander.String(),
                                         title=_(u"UserID or email address."))
            password = colander.SchemaNode(colander.String(),
                                           title=_('Password'),
                                           widget=deform.widget.PasswordWidget(size=20),)
            came_from = came_from_node

        return LoginSchema()

    if type in ('add', 'registration'):
        if not IUsers.providedBy(context):
            raise TypeError("context for a user registration must be an object that implements IUsers.")
        
        def _userid_validation(node, value):
            """ Context-dependent userid validation.
                Check that userid is:
                - unique
                - doesn't contain bogus chars
            """
            pattern = re.compile(r'^[a-zA-Z]{1}[\w-]{1,14}$')
            if not pattern.match(value):
                raise colander.Invalid(node, _('userid_char_error', default=u"UserID must be 3-15 chars, start with a-zA-Z and only contain regular latin chars, numbers, minus and underscore."))
            if value in context:
                raise colander.Invalid(node, _('already_registered_error',
                                               default=u"UserID already registered. If it was registered by you, try to retrieve your password."))

        class AddUserSchema(colander.Schema):
            userid = colander.SchemaNode(colander.String(),
                                         title = _(u"UserID"),
                                         description = _('userid_description', default=u"Used like a nick-name and as a unique id. You can't change this later."),
                                         validator=_userid_validation)
            password = password_node
            email = email_node
            first_name = first_name_node
            last_name = last_name_node
            came_from = came_from_node
        return AddUserSchema()

    if type == 'edit':
        class EditUserSchema(colander.Schema):
            email = email_node
            first_name = first_name_node
            last_name = last_name_node
            biography = colander.SchemaNode(colander.String(),
                title = _(u"About you"),
                description = _('bio_visible_notice',
                                default=u"Please note that anything you type here will be visible to all registered users, even if they're not in the same meeting as you."),
                widget = deform.widget.TextAreaWidget(rows=10, cols=60),
                missing=u"",
                validator=html_string_validator,)
        return EditUserSchema()

    if type == 'change_password':
        class ChangePasswordSchema(colander.Schema):
            password = password_node
        return ChangePasswordSchema()
    
    if type == 'request_password':
        class RequestNewPasswordSchema(colander.Schema):
            userid_or_email = colander.SchemaNode(colander.String(),
                                                  title = _(u"UserID or email address."))
        return RequestNewPasswordSchema()
    
    if type == 'token_password_change':
        class TokenPasswordChangeSchema(colander.Schema):
            #FIXME: Implement captcha here to avoid bruteforce
            token = colander.SchemaNode(colander.String(),
                                        validator = context.validate_password_token,
                                        missing = u'',
                                        widget = deform.widget.HiddenWidget(),)
            password = password_node
        return TokenPasswordChangeSchema()

    #No schema found
    raise KeyError("No schema found of type: '%s'" % type)


def includeme(config):
    from voteit.core.app import register_content_info
    register_content_info(construct_schema, User, registry=config.registry)
