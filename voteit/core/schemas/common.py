from datetime import timedelta
from uuid import uuid4
import re

from pyramid.traversal import find_resource
from pyramid.traversal import find_root
from six import string_types
import colander
import deform

from voteit.core import _


NAME_PATTERN = re.compile(r'^[\w\s]{3,100}$', flags=re.UNICODE)
#For when it's part of a http GET - no # in front of it
HASHTAG_PATTERN = re.compile(r'^[\w\s_\-]{1,100}$', flags=re.UNICODE)


@colander.deferred
def random_oid(*args):
    """ This is a really silly way to get a random form field.
        Deform doesn't have this feature, and will cause fields ids to collide if used on the same page.
    """
    return str(uuid4())

@colander.deferred
def deferred_default_start_time(node, kw):
    request = kw['request']
    return request.dt_handler.localnow()

@colander.deferred
def deferred_default_end_time(node, kw):
    request = kw['request']
    return request.dt_handler.localnow() + timedelta(hours=24)

@colander.deferred
def deferred_default_user_fullname(node, kw):
    """ Return users fullname, if the user exist. """
    request = kw['request']
    if request.profile:
        return request.profile.title
    return ''

@colander.deferred
def deferred_default_user_email(node, kw):
    """ Return users email, if the user exist. """
    request = kw['request']
    if request.profile:
        return request.profile.email
    return ''

@colander.deferred
def deferred_default_hashtag_text(node, kw):
    """ If this is a reply to something else, the default value will
        contain the userid of the original poster + any hashtags used.
    """
    request = kw['request']
    output = u""
    tags = []
    for rtag in request.GET.getall('tag'):
        if HASHTAG_PATTERN.match(rtag):
            tags.append(rtag)
    reply_to = request.GET.get('reply-to', None)
    if reply_to:
        for docid in request.root.catalog.search(uid = reply_to)[1]:
            path = request.root.document_map.address_for_docid(docid)
            obj = find_resource(request.root, path)
            if obj.type_name == 'DiscussionPost':
                output += "".join(["@%s: " % x for x in obj.creators])
            for tag in obj.tags:
                if tag not in tags:
                    tags.append(tag)
    output += " ".join(["#%s" % x for x in tags])
    return output

def strip_whitespace(value):
    """ Used as preparer - strips whitespace from the end of rows. """
    if not isinstance(value, string_types):
        return value
    return "\n".join([x.strip() for x in value.splitlines()])

def strip_and_lowercase(value):
    """ Used as preparer - strips whitespace from the end of rows and lowercases all content. """
    if not isinstance(value, basestring):
        return value
    return "\n".join([x.strip().lower() for x in value.splitlines()])

@colander.deferred
def deferred_autocompleting_userid_widget(node, kw):
    context = kw['context']
    root = find_root(context)
    choices = tuple(root.users.keys())
    return deform.widget.AutocompleteInputWidget(
        size=15,
        values = choices,
        min_length=1)
