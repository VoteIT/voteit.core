import colander
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface
from betahaus.pyracont.decorators import schema_factory

from voteit.core.models.interfaces import ISiteRoot
from voteit.core.schemas.common import came_from_node
from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator
from voteit.core.validators import deferred_unique_email_validator
from voteit.core.validators import deferred_new_userid_validator


def fetch_userid(value):
    """ A preparer to fetch userid at login, in case an email address is used. """
    if not value:
        return value
    request = get_current_request()
    context = getattr(request, 'context')
    if context is None:
        return value
    root = find_interface(context, ISiteRoot)
    if '@' in value:
        user = root.users.get_user_by_email(value)
        if user is None:
            return value
        return user.userid
    return value

def to_lowercase(value):
    """ For things that should always be lowercase. (UserID, Email etc) """
    if isinstance(value, basestring):
        return value.lower()
    return value

def userid_node():
    return colander.SchemaNode(colander.String(),
                               title = _(u"UserID"),
                               description = _('userid_description',
                                               default=u"Used as a nickname, in @-links and as a unique id. "
                                                       u"You can't change this later. OK characters are: a-z, 0-9, '.', '-', '_'."),
                               validator=deferred_new_userid_validator,)

def email_node():
    return colander.SchemaNode(colander.String(),
                               title=_(u"Email"),
                               validator=deferred_unique_email_validator,
                               preparer=to_lowercase,)

def first_name_node():
    return colander.SchemaNode(colander.String(),
                               title = _(u"First name"),
                               validator = html_string_validator,)

def last_name_node():
    return colander.SchemaNode(colander.String(),
                               title = _(u"Last name"),
                               missing = u"",
                               validator = html_string_validator,)


@schema_factory('LoginSchema', title = _(u"Login"))
class LoginSchema(colander.Schema):
    userid = colander.SchemaNode(colander.String(),
                                 preparer = fetch_userid,
                                 title = _(u"UserID or email address."))
    came_from = came_from_node()


@schema_factory('RegisterSchema', title = _(u"Registration"))
class RegisterSchema(colander.Schema):
    """ Used for registration. """
    userid = colander.SchemaNode(colander.String(),
                                 title = _(u"UserID"),
                                 description = _('userid_description',
                                                 default=u" Used as a nickname, in @-links and as a unique id. You can't change this later. OK characters are: a-z, 0-9, '.', '-', '_'."),
                                 validator = deferred_new_userid_validator,
                                 preparer = to_lowercase,)
    email = email_node()
    first_name = first_name_node()
    last_name = last_name_node()
    came_from = came_from_node()
