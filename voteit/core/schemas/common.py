import re
from datetime import timedelta

import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from pyramid.testing import DummyRequest
from pyramid.traversal import find_root
from pyramid.traversal import resource_path

from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.validators import deferred_csrf_token_validator
from voteit.core import VoteITMF as _


NAME_PATTERN = re.compile(r'^[\w\s]{3,100}$', flags=re.UNICODE)
#For when it's part of a http GET - no # in front of it
HASHTAG_PATTERN = re.compile(r'^[\w\s_\-]{1,100}$', flags=re.UNICODE)


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
    #FIXME: Missing tests
    context = kw['context']
    if not hasattr(context, 'get_tags'):
        return u""
    tags = context.get_tags()
    return tags and u" ".join(tags) or u""

@colander.deferred
def deferred_default_hashtag_text(node, kw):
    """ If this is a reply to something else, the default value will
        contain the userid of the original poster + any hashtags used.
    """
    context = kw['context']
    request = kw['request']
    output = u""
    request_tag = request.GET.get('tag', None)
    if request_tag:
        if not HASHTAG_PATTERN.match(request_tag):
            request_tag = None #Blank it, since it's invalid!
    if IAgendaItem.providedBy(context):
        #This is a first post - don't add any hashtags or similar,
        #unless they're part of query string
        if request_tag:
            output += u"#%s" % request_tag
        return output
    # get creator of answered object
    creators = context.get_field_value('creators')
    if creators:
        output += u"@%s: " % creators[0]
    # get tags and make a string of them
    tags = list(context.get_tags([]))
    if request_tag and request_tag not in tags:
        tags.append(request_tag)
    for tag in tags:
        output += u" #%s" % tag
    return output

def strip_whitespace(value):
    """ Used as preparer - strips whitespace from the end of rows. """
    if not isinstance(value, basestring):
        return value
    return "\n".join([x.strip() for x in value.splitlines()])

def strip_and_lowercase(value):
    """ Used as preparer - strips whitespace from the end of rows and lowercases all content. """
    if not isinstance(value, basestring):
        return value
    return "\n".join([x.strip().lower() for x in value.splitlines()])

def add_csrf_token(context, request, schema):
    """ Append csrf-token to schema, if it isn't added by a testing script. """
    #Make sure this is not a blank testing request
    if isinstance(request, DummyRequest) and request.session.get_csrf_token() == 'csrft':
        return
    schema.add(colander.SchemaNode(
                   colander.String(),
                   name="csrf_token",
                   widget = deform.widget.HiddenWidget(),
                   default = deferred_default_csrf_token,
                   validator = deferred_csrf_token_validator,
                   )
               )

@colander.deferred
def deferred_default_csrf_token(node, kw):
    request = kw['request']
    return request.session.get_csrf_token()

@colander.deferred
def deferred_autocompleting_userid_widget(node, kw):
    context = kw['context']
    root = find_root(context)
    choices = tuple(root.users.keys())
    return deform.widget.AutocompleteInputWidget(
        size=15,
        values = choices,
        min_length=1)
