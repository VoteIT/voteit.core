import warnings
from datetime import timedelta
from uuid import uuid4
import re

import deform
from arche.widgets import deferred_autocompleting_userid_widget, UserReferenceWidget  # b/c
from pyramid.traversal import find_resource, find_interface
from six import string_types
import colander

from voteit.core import _
from voteit.core.models.interfaces import IMeeting

NAME_PATTERN = re.compile(r'^[\w\s]{3,100}$', flags=re.UNICODE)
#For when it's part of a http GET - no # in front of it
HASHTAG_PATTERN = re.compile(r'^[\w_\-]{1,100}$', flags=re.UNICODE)


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


def prepare_emails_from_text(value):
    """ Used as preparer - strips whitespace from the end of rows and lowercases all content. """
    if not isinstance(value, basestring):
        return value
    value = re.sub("[,;]", "", value)
    value = value.lower()
    res = []
    for x in value.splitlines():
        x = x.strip()
        if x:
            res.append(x)
    return "\n".join(res)


def collapsible_limit_node():
    return colander.SchemaNode(
        colander.Int(),
        title=_("Collapse body texts that are higher than..."),
        widget=deform.widget.SelectWidget(values=(
            # The odd values here are so we can have a sane default
            ('0', _("Off")),
            ('', _("Default (200px)")),
            ('400', "400px"),
            ('600', "600px"),
            ('800', "800px"),
        )),
        missing=None,
    )


def strip_and_lowercase(value):
    warnings.warn('strip_and_lowercase renamed prepare_emails_from_text', DeprecationWarning)
    return prepare_emails_from_text(value)


class MeetingUserReferenceWidget(UserReferenceWidget):
    view_name = "users_search_select2.json"  # The view to query
    context_from = 'get_meeting'

    def get_meeting(self, bindings):
        return find_interface(bindings["context"], IMeeting)
