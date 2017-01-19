import re

from BeautifulSoup import BeautifulSoup
from pyramid.traversal import find_interface
from translationstring import TranslationString
from webhelpers.html.tools import strip_tags
import colander

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.user import USERID_REGEXP
from voteit.core.security import VIEW
from voteit.core.security import find_authorized_userids


AT_USERID_PATTERN = re.compile(r'(\A|\s)@('+USERID_REGEXP+r')')
NEW_USERID_PATTERN = re.compile(r'^'+USERID_REGEXP+r'$')


def html_string_validator(node, value):
    """ Checks that input doesn't contain html tags
    """
    # removes tags and new lines and replaces <br> with newlines
    svalue = strip_tags(value)
    # removes newlines
    svalue = re.sub(r"\r?\n", " ", svalue)
    value = re.sub(r"\r?\n", " ", value)
    # removes duplicated whitespaces
    svalue = ' '.join(svalue.split())
    value = ' '.join(value.split())
    # if the original value and the stripped value is not the same raise exception
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
        invalid = set()
        matched_userids = set()
        #Note: First match object will be blankspace, second the userid.
        [matched_userids.add(x[1]) for x in re.findall(AT_USERID_PATTERN, value)]
        if not matched_userids:
            return
        #Check that user exists in meeting
        meeting = find_interface(self.context, IMeeting)
        valid_userids =  find_authorized_userids(meeting, (VIEW,))
        for userid in matched_userids:
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


class TokenFormValidator(object):
    def __init__(self, context):
        assert IMeeting.providedBy(context)
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


def richtext_validator(node, value):
    """
        checks that input doesn't contain forbidden html tags
    """
    INVALID_TAGS = ['textarea', 'select', 'option', 'input', 'button', 'script']
    soup = BeautifulSoup(value)
    invalid = False
    for tag in soup.findAll(True):
        if tag.name in INVALID_TAGS:
            invalid = True
    if invalid:
        raise colander.Invalid(node, _(u"Contains forbidden HTML tags."))


# @colander.deferred
# def deferred_context_roles_validator(node, kw):
#     context = kw['context']
#     request = kw['request']
#     return ContextRolesValidator(context, request)
# 
# 
# class ContextRolesValidator(object):
#     """ Check that the roles a user tries to assign is allowed in this context.
#     """
#     
#     def __init__(self, context, request):
#         self.context = context
#         self.request = request
#     
#     def __call__(self, node, value):
#         if not has_permission(MANAGE_GROUPS, self.context, self.request):
#             raise colander.Invalid(node, _(u"You can't change groups in this context"))
#         roles = []
#         if ISiteRoot.providedBy(self.context):
#             roles.extend([x[0] for x in ROOT_ROLES])
#         elif IMeeting.providedBy(self.context):
#             roles.extend([x[0] for x in MEETING_ROLES])
#         for v in value:
#             if v not in roles:
#                 raise colander.Invalid(node, _(u"wrong_context_for_roles_error",
#                                                default = u"Group ${group} can't be assigned in this context",
#                                                mapping = {'group': v}))


class NotOnlyDefaultTextValidator(object):
    """ Validator which fails if only default text or only tag is pressent
    """
    def __init__(self, context, request, default_deferred):
        self.context = context
        self.request = request
        self.default_deferred = default_deferred

    def __call__(self, node, value):
        # since colander.All doesn't handle deferred validators we call the validator for AtEnabledTextArea here 
        at_enabled_validator = AtEnabledTextArea(self.context)
        at_enabled_validator(node, value)
        default = self.default_deferred(node, {'context': self.context, 'request': self.request})
        if isinstance(default, TranslationString):
            default = self.request.localizer.translate(default)
        if value.strip() == default.strip():
            raise colander.Invalid(node, _(u"only_default_text_validator_error",
                                           default=u"Only the default content is not valid",))
