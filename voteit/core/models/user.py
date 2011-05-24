import re
from hashlib import sha1

from BTrees.OOBTree import OOBTree
import colander
import deform
from zope.interface import implements
from repoze.folder import unicodify
from pyramid.security import Allow

from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers
from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.validators import password_validation
from pyramid.traversal import find_interface


def get_sha_password(password):
    """ Encode a plaintext password to sha1. """
    if isinstance(password, unicode):
        password = password.encode('UTF-8')
    return 'SHA1:' + sha1(password).hexdigest()


class User(BaseContent):
    """ Content type for a user. Usable as a profile page. """
    implements(IUser)
    content_type = 'User'
    allowed_contexts = ('Users',)
    add_permission = security.ADD_USER
    
    __acl__ = [(Allow, security.ROLE_ADMIN, security.EDIT),
               (Allow, security.ROLE_OWNER, [security.EDIT, security.CHANGE_PASSWORD])]

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


def construct_schema(**kwargs):
    context = kwargs.get('context', None)
    type = kwargs.get('type', None)
    if context is None:
        KeyError("'context' is a required keyword for User schemas. See construct_schema in the user module.")    
    if type is None:
        KeyError("'type' is a required keyword for User schemas. See construct_schema in the user module.")    
        
    def _validate_email(node, value):
        default_email_validator = colander.Email(msg=_(u"Invalid email"))
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
                        validator=password_validation,
                        widget=deform.widget.CheckedPasswordWidget(size=20),
                        title=_('Password'))
    email_node = colander.SchemaNode(colander.String(),
                                     title=_(u"Email"),
                                     validator=_validate_email,)
    first_name_node = colander.SchemaNode(colander.String(),
                                          title=_(u"First name"),)
    last_name_node = colander.SchemaNode(colander.String(),
                                         title=_(u"Last name"),
                                         missing=u"",)


    if type == 'login':
        class LoginSchema(colander.Schema):
            userid = colander.SchemaNode(colander.String(),
                                         title=_(u"UserID or email address."))
            password = colander.SchemaNode(colander.String(),
                                           title=_('Password'),
                                           widget=deform.widget.PasswordWidget(size=20),)
            came_from = colander.SchemaNode(
                        colander.String(),
                        widget = deform.widget.HiddenWidget(),
                        default='/',)
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
                raise colander.Invalid(node, _(u"UserID must be 3-15 chars, start with a-zA-Z and only contain regular latin chars, numbers, minus and underscore."))
            if value in context:
                raise colander.Invalid(node, _(u"UserID already registered. If it was registered by you, try to retrieve your password."))

        class AddUserSchema(colander.Schema):
            userid = colander.SchemaNode(colander.String(),
                                         title = _(u"UserID"),
                                         description = _(u"Used like a nick-name and as a unique id. You can't change this later."),
                                         validator=_userid_validation)
            password = password_node
            email = email_node
            first_name = first_name_node
            last_name = last_name_node
        return AddUserSchema()

    if type == 'edit':
        class EditUserSchema(colander.Schema):
            email = email_node
            first_name = first_name_node
            last_name = last_name_node
            biography = colander.SchemaNode(colander.String(),
                title = _(u"About you"),
                description = _(u"Please note that anything you type here will be visible to all registered users."),
                widget = deform.widget.TextAreaWidget(rows=10, cols=60),
                missing=u"")
        return EditUserSchema()

    if type == 'change_password':
        class ChangePasswordSchema(colander.Schema):
            password = password_node
        return ChangePasswordSchema()

    #No schema found
    raise KeyError("No schema found of type: '%s'" % type)


def includeme(config):
    from voteit.core import register_content_info
    register_content_info(construct_schema, User, registry=config.registry)
