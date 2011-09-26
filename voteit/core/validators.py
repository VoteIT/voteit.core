import re
import colander
from webhelpers.html.tools import strip_tags
from webhelpers.html.converters import nl2br
from pyramid.traversal import find_interface, find_root

from voteit.core.models.interfaces import IMeeting
from voteit.core.security import find_authorized_userids
from voteit.core.security import VIEW
from voteit.core import VoteITMF as _


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
    svalue = re.sub(r"\r?\n"," ", svalue)
    value = re.sub(r"\r?\n"," ", value)
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


def at_userid_validator(node, value, obj):
    """
        checks that the userid in '@userid' realy is a userid in the system
    """
    meeting = find_interface(obj, IMeeting)

    from voteit.core.models.user import userid_regexp
    regexp = r'(\A|\s)@('+userid_regexp+r')'

    reg = re.compile(regexp)
    invalid = []
    for (space, userid) in re.findall(regexp, value):
        #Check if requested userid has permission in meeting
        if not userid in find_authorized_userids(meeting, (VIEW,)):
            invalid.append(userid)
            
    if invalid:
        userids = ", ".join(invalid)
        raise colander.Invalid(node, _(u"The following userids is invalid: ${userids}", mapping={'userids': userids}))
