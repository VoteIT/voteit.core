import re
from datetime import timedelta

import colander

from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.models.interfaces import IAgendaItem


NAME_PATTERN = re.compile(r'^[\w\s]{3,100}$', flags=re.UNICODE)


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

@colander.deferred
def deferred_default_tags(node, kw):
    #FIXME: Accessing tags this way is wrong - rewrite!
    #FIXME: Missing tests
    context = kw['context']
    if hasattr(context, '_tags'):
        return u" ".join(context._tags)
    return u""

@colander.deferred
def deferred_default_hashtag_text(node, kw):
    """ If this is a reply to something else, the default value will
        contain the userid of the original poster + any hashtags used.
    """
    context = kw['context']
    output = u""
    if IAgendaItem.providedBy(context):
        #This is a first post - don't add any hashtags or similar
        return output
    # get creator of answered object
    creators = context.get_field_value('creators')
    if creators:
        output += "@%s: " % creators[0]
    # get tags and make a string of them
    #FIXME: Don't use private attr _tags - REWRITE!
    for tag in getattr(context, '_tags', ()):
        output += " #%s" % tag
    return output

def strip_whitespace(value):
    """ Used as preparer - strips whitespace from the end of rows. """
    if not isinstance(value, basestring):
        return value
    return "\n".join([x.strip() for x in value.splitlines()])
