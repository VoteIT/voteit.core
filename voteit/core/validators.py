import re
import colander
from webhelpers.html.tools import strip_tags
from webhelpers.html.converters import nl2br

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

