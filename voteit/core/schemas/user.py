from urllib import quote

import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from betahaus.pyracont.factories import createContent

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IProfileImage
from voteit.core.validators import html_string_validator
from voteit.core.validators import deferred_unique_email_validator
from voteit.core.validators import password_validation
from voteit.core.validators import deferred_new_userid_validator
from voteit.core.validators import deferred_password_token_validator
from voteit.core.validators import deferred_current_password_validator
from voteit.core import security 
from voteit.core.widgets import RecaptchaWidget


@colander.deferred
def deferred_recaptcha_widget(node, kw):
    """ No recaptcha if captcha settings is now present or if the current user is an admin 
    """
    context = kw['context']
    request = kw['request']
    api = kw['api']
    
    # Get principals for current user
    principals = api.context_effective_principals(context)
    
    if api.root.get_field_value('captcha_registration', False) and security.ROLE_ADMIN not in principals:
        return RecaptchaWidget(api.root.get_field_value('captcha_public_key', ''), 
                               api.root.get_field_value('captcha_private_key', ''))

    return deform.widget.HiddenWidget()

@colander.deferred
def deferred_referer(node, kw):
    request = kw['request']
    return quote(request.GET.get('came_from', '/'))

def userid_preparer(value):
    return value.lower()

def userid_node():
    return colander.SchemaNode(colander.String(),
                               title = _(u"UserID"),
                               description = _('userid_description',
                                               default=u"Used as a nickname, in @-links and as a unique id. You can't change this later. OK characters are: a-z, 0-9, '.', '-', '_'."),
                               validator=deferred_new_userid_validator,)

def password_node():
    return colander.SchemaNode(colander.String(),
                               validator=colander.All(password_validation, html_string_validator,),
                        widget=deform.widget.CheckedPasswordWidget(size=20),
                        title=_('Password'))

def email_node():
    return colander.SchemaNode(colander.String(),
                               title=_(u"Email"),
                               validator=deferred_unique_email_validator,)

def first_name_node():
    return colander.SchemaNode(colander.String(),
                               title=_(u"First name"),
                               validator=html_string_validator,)

def last_name_node():
    return colander.SchemaNode(colander.String(),
                               title=_(u"Last name"),
                               missing=u"",
                               validator=html_string_validator,)


def came_from_node():
    return colander.SchemaNode(colander.String(),
                               missing=u"",
                               widget = deform.widget.HiddenWidget(),
                               default=deferred_referer)

def recaptcha_node():
    return colander.SchemaNode(colander.String(),
                               #FIXME: write a good title and description here
                               title=_(u"Verify you are human"),
                               description = _(u"registration_captcha_description",
                                               default=u"This is to prevent spambots from register"),
                               missing=u"",
                               widget=deferred_recaptcha_widget,)
    
@colander.deferred
def profile_image_plugin_choices_widget(node, kw):
    context = kw['context']
    request = kw['request']
    api = kw['api']

    user = api.user_profile
    plugin_choices = set()
    for (name, adapter) in request.registry.getAdapters((user,), IProfileImage):
        if adapter.is_valid_for_user():
            plugin_choices.add((name, adapter.title))

    return deform.widget.RadioChoiceWidget(values=plugin_choices)

@colander.deferred
def deferred_default_profile_image_plugin(node, kw):
    request = kw['request']
    return 'gravatar_profile_image'

@colander.deferred
def deferred_local_profile_information_widget(node, kw):
    """ Fetch any keys in auth_domains. """
    context = kw['context']
    choices = [(x, x) for x in context.auth_domains.keys()]
    return deform.widget.CheckboxChoiceWidget(values=choices,
                                              null_value = ())


@schema_factory('AddUserSchema', title = _(u"Add user"), description = _(u"Use this form to add a user"))
class AddUserSchema(colander.Schema):
    """ Used for regular add command. """
    userid = colander.SchemaNode(colander.String(),
                                 title = _(u"UserID"),
                                 description = _('userid_description',
                                                 default=u" Used as a nickname, in @-links and as a unique id. You can't change this later. OK characters are: a-z, '.', '-', '_'."),
                                 validator=deferred_new_userid_validator,
                                 preparer=userid_preparer,)

    password = password_node()
    email = email_node()
    first_name = first_name_node()
    last_name = last_name_node()
    came_from = came_from_node()


@schema_factory('RegisterUserSchema', title = _(u"Registration"))
class RegisterUserSchema(colander.Schema):
    """ Used for registration. """
    userid = colander.SchemaNode(colander.String(),
                                 title = _(u"UserID"),
                                 description = _('userid_description',
                                                 default=u" Used as a nickname, in @-links and as a unique id. You can't change this later. OK characters are: a-z, 0-9, '.', '-', '_'."),
                                 validator=deferred_new_userid_validator,
                                 preparer=userid_preparer,)
    password = password_node()
    email = email_node()
    first_name = first_name_node()
    last_name = last_name_node()
    came_from = came_from_node()
    captcha = recaptcha_node();


@schema_factory('EditUserSchema', title = _(u"Edit user"), description = _(u"Use this form to edit a user"))
class EditUserSchema(colander.Schema):
    """ Regular edit. """
    email = email_node()
    first_name = first_name_node()
    last_name = last_name_node()
    about_me = colander.SchemaNode(colander.String(),
        title = _(u"About me"),
        description = _(u"user_about_me_description",
                        default=u"Please note that anything you type here will be visible to all users in the same meeting as you."),
        widget = deform.widget.TextAreaWidget(rows=10, cols=60),
        missing=u"",
        validator=html_string_validator,)
    profile_image_plugin = colander.SchemaNode(colander.String(),
                                               title = _(u"Profile image provider"),
                                               description = _(u"profile_image_plugin_description",
                                                               default=u""),
                                               widget = profile_image_plugin_choices_widget,
                                               default = deferred_default_profile_image_plugin,) 


@schema_factory('LoginSchema', title = _(u"Login"))
class LoginSchema(colander.Schema):
    userid = colander.SchemaNode(colander.String(),
                                 title=_(u"UserID or email address."))
    password = colander.SchemaNode(colander.String(),
                                   title=_('Password'),
                                   widget=deform.widget.PasswordWidget(size=20),)
    came_from = came_from_node()


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


@schema_factory('ManageConnectedProfilesSchema', title = _(u"Manage connected profiles"),
                description = _(u"manage_connected_profiles_schema_description",
                                default = u"You can remove local authentication information for any connected services. "
                                u"This will make you unable to login with that service. "
                                u"Be sure to have other means of login in before doing so!"))
class ManageConnectedProfilesSchema(colander.Schema):
    auth_domains = colander.SchemaNode(deform.Set(allow_empty = True),
                                       title = u"Remove domains?",
                                       missing = colander.null,
                                       widget = deferred_local_profile_information_widget,)
