import re
import colander
from webhelpers.html.tools import strip_tags
from pyramid.traversal import find_interface
from pyramid.traversal import find_root

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IUser
from voteit.core.security import find_authorized_userids
from voteit.core.security import VIEW
from voteit.core import VoteITMF as _
from voteit.core.models.user import USERID_REGEXP


AT_USERID_PATTERN = re.compile(r'(\A|\s)@('+USERID_REGEXP+r')')
NEW_USERID_PATTERN = re.compile(r'^'+USERID_REGEXP+r'$')


def password_validation(node, value):
    """ check that password is
        - at least 6 chars and at most 100.
    """
    if len(value) < 6:
        raise colander.Invalid(node, _(u"Too short. At least 6 chars required."))
    if len(value) > 100:
        raise colander.Invalid(node, _(u"Less than 100 chars please."))


def html_string_validator(node, value):
    """
        checks that input doesn't contain html tags
    """
    # removes tags and new lines and replaces <br> with newlines
    svalue = strip_tags(value)
    # removes newlines
    svalue = re.sub(r"\r?\n", " ", svalue)
    value = re.sub(r"\r?\n", " ", value)
    # removes duplicated whitespaces
    svalue = ' '.join(svalue.split())
    value = ' '.join(value.split())
    # if the original value and the stript value is not the same rais exception
    if not svalue == value:
        raise colander.Invalid(node, _(u"HTML is not allowed."))


def multiple_email_validator(node, value):
    """
        checks that each line of value is a correct email
    """

    validator = colander.Email()
    invalid = []
    for email in value.splitlines():
        try:
            validator(node, email)
        except colander.Invalid:
            invalid.append(email)
            
    if invalid:
        emails = ", ".join(invalid)
        raise colander.Invalid(node, _(u"The following adresses is invalid: ${emails}", mapping={'emails': emails}))


class AtEnabledTextArea(object):
    """ Validator which succeeds if @-sign points to a user that exists in this meeting.
        Also checks that text doesn't contain evil chars :)
    """
    def __init__(self, context):
        self.context = context

    def __call__(self, node, value):
        #First, check for bad chars, since it requires less CPU
        html_string_validator(node, value)
        #Check that user exists in meeting
        meeting = find_interface(self.context, IMeeting)
        invalid = set()
        valid_userids =  find_authorized_userids(meeting, (VIEW,))
        for (space, userid) in re.findall(AT_USERID_PATTERN, value):
            #Check if requested userid has permission in meeting
            if not userid in valid_userids:
                invalid.add(userid)
                
            if invalid:
                userids = ", ".join(invalid)
                raise colander.Invalid(node, _(u"userid_validator_error",
                                               default=u"The following userids is invalid: ${userids}. Remember that userids are case sensitive.",
                                               mapping={'userids': userids}))

@colander.deferred
def deferred_at_enabled_text(node, kw):
    context = kw['context']
    return AtEnabledTextArea(context)


class NewUniqueUserID(object):
    """ Check if UserID is unique globally in the site and that UserID conforms to correct standard. """
    
    def __init__(self, context):
        self.context = context

    def __call__(self, node, value):
        if not NEW_USERID_PATTERN.match(value):
            msg = _('userid_char_error',
                    default=u"UserID must be 3-15 chars, start with a-zA-Z and only contain regular latin chars, numbers, minus and underscore.")
            raise colander.Invalid(node, msg)
        
        root = find_root(context)
        if value in root.users:
            msg = _('already_registered_error',
                    default=u"UserID already registered. If it was registered by you, try to retrieve your password.")
            raise colander.Invalid(node, msg)
        

@colander.deferred
def deferred_new_userid_validator(node, kw):
    context = kw['context']
    return NewUniqueUserID(context)


class UniqueEmail(object):
    """ Check that email address is valid and unique. """
    
    def __init__(self, context):
        self.context = context
    
    def __call__(self, node, value):        
        default_email_validator = colander.Email(msg=_(u"Invalid email address."))
        default_email_validator(node, value)
        #context can be IUser or IUsers
        users = find_interface(context, IUsers)
        #User with email exists?
        match = users.get_user_by_email(value)
        if match and context != match:
            #Something was found, and it isn't this context - I.e. some other user
            msg = _(u"email_not_unique_error",
                    default=u"Another user has already registered with that email address. If you've lost your password, request a new one instead.")
            raise colander.Invalid(node, 
                                   msg)

        
@colander.deferred
def deferred_unique_email_validator(node, kw):
    context = kw['context']
    return UniqueEmail(context)


class CheckPasswordToken(object):
    def __init__(self, context):
        assert IUser.providedBy(context)
        self.context = context
    
    def __call__(self, node, value):
        return self.context.validate_password_token(node, value)


@colander.deferred
def deferred_password_token_validator(node, kw):
    context = kw['context']
    return CheckPasswordToken(context)


class TokenFormValidator(object):
    def __init__(self, context):
        self.context = context
    
    def __call__(self, form, value):
        email = value['email']
        token = self.context.invite_tickets.get(email)
        if not token:
            exc = colander.Invalid(form, 'Incorrect email')
            exc['token'] = _(u"Couldn't find any invitation for this email address.")
            raise exc

        if token.token != value['token']:
            exc = colander.Invalid(form, _(u"Email matches, but token doesn't"))
            exc['token'] = _(u"Check this field - token doesn't match")
            raise exc


@colander.deferred
def deferred_token_form_validator(form, kw):
    context = kw['context']
    return TokenFormValidator(context)
