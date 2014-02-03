import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from pyramid.traversal import find_root

from voteit.core.validators import html_string_validator
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import ISiteRoot
from voteit.core import VoteITMF as _
from .interfaces import IPasswordHandler


def password_validation(node, value):
    """ check that password is
        - at least 6 chars and at most 100.
    """
    if len(value) < 6:
        raise colander.Invalid(node, _(u"Too short. At least 6 chars required."))
    if len(value) > 100:
        raise colander.Invalid(node, _(u"Less than 100 chars please."))


class CurrentPasswordValidator(object):
    """ Check that current password matches. Used for sensitive operations
        when logged in to make sure that no one else changes the password for instance.
    """
    
    def __init__(self, context):
        assert IUser.providedBy(context) # pragma : no cover
        self.context = context
    
    def __call__(self, node, value):
        pw_field = self.context.get_custom_field('password')
        if not pw_field.check_input(value):
            raise colander.Invalid(node, _(u"Current password didn't match"))


@colander.deferred
def deferred_current_password_validator(node, kw):
    context = kw['context']
    return CurrentPasswordValidator(context)


class CheckPasswordToken(object):
    #FIXME: This validator is probably not needed. We should hook into the adapter directly
    def __init__(self, context, request):
        assert IUser.providedBy(context)
        self.context = context
        self.request = request
    
    def __call__(self, node, value):
        pw_handler = self.request.registry.getAdapter(self.context, IPasswordHandler)
        pw_handler.token_validator(node, value)


@colander.deferred
def deferred_password_token_validator(node, kw):
    context = kw['context']
    request = kw['request']
    return CheckPasswordToken(context, request)


class LoginPasswordValidator(object):
    """ Make sure a user exist and check that users password. This is a validator for a form,
        since it checks the field userid and password.
        
        Displaying information about bad password or userid might not be a good idea, so we won't do that now.
    """
    def __init__(self, context):
        assert ISiteRoot.providedBy(context)
        self.context = context
    
    def __call__(self, form, value):
        password = value['password']
        userid = value['userid'] #Might be an email address!
        exc = colander.Invalid(form, u"Login invalid") #Raised if trouble
        #First, retrieve user object
        user = self.context.users.get(userid)
        if user is None:
            exc['userid'] = _(u"Not found.")
            raise exc
        #Validate password
        pw_field = user.get_custom_field('password')
        if not pw_field.check_input(password):
            exc['password'] = _(u"Wrong password. Remember that passwords are case sensitive.")
            raise exc


@colander.deferred
def deferred_login_password_validator(form, kw):
    context = kw['context']
    root = find_root(context)
    return LoginPasswordValidator(root)


def password_node():
    return colander.SchemaNode(colander.String(),
                               validator=colander.All(password_validation, html_string_validator,),
                        widget=deform.widget.CheckedPasswordWidget(size=20),
                        title=_('Password'),
                        description = _(u"password_creation_tip",
                                        default = u"Use at least 6 chars. A good rule is to use long passwords that "
                                                  u"doesn't contain any personal information or things that someone else might guess."))


@schema_factory('ChangePasswordSchema', title = _(u"Change password"))
class ChangePasswordSchema(colander.Schema):
    current_password = colander.SchemaNode(colander.String(),
                                   title=_('Current password'),
                                   widget=deform.widget.PasswordWidget(size=20),
                                   validator=deferred_current_password_validator)
    password = password_node()


@schema_factory('ChangePasswordAdminSchema', title = _(u"Change password"), description = _(u"Use this form to change password"))
class ChangePasswordAdminSchema(colander.Schema):
    password = password_node()


@schema_factory('RequestNewPasswordSchema', title = _(u"Request new password"), description = _(u"Use this form to request a new password"))
class RequestNewPasswordSchema(colander.Schema):
    userid_or_email = colander.SchemaNode(colander.String(),
                                          title = _(u"UserID or email address."))


@schema_factory('TokenPasswordChangeSchema')
class TokenPasswordChangeSchema(colander.Schema):
    #FIXME: Implement captcha here to avoid bruteforce
    token = colander.SchemaNode(colander.String(),
                                validator = deferred_password_token_validator,
                                missing = u'',
                                widget = deform.widget.HiddenWidget(),)
    password = password_node()
