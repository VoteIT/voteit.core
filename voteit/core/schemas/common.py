from datetime import timedelta

import colander
import deform
from pyramid.traversal import find_root

from voteit.core.models.interfaces import IDateTimeUtil


@colander.deferred
def deferred_default_start_time(node, kw):
    request = kw['request']
    dt_util = request.registry.getUtility(IDateTimeUtil)
    return dt_util.localnow()


@colander.deferred
def deferred_default_end_time(node, kw):
    request = kw['request']
    dt_util = request.registry.getUtility(IDateTimeUtil)
    return dt_util.localnow() + timedelta(hours=24)


@colander.deferred
def deferred_default_user_fullname(node, kw):
    """ Return users fullname, if the user exist. """
    api = kw['api']
    user = api.get_user(api.userid)
    if user:
        return user.title
    return u''

@colander.deferred
def deferred_default_user_email(node, kw):
    """ Return users email, if the user exist. """
    api = kw['api']
    user = api.get_user(api.userid)
    if user:
        return user.get_field_value('email')
    return u''

def strip_whitespace(value):
    return "\n".join([x.strip() for x in value.splitlines()])
