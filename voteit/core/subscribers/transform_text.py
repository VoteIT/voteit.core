# -*- coding: utf-8 -*-

import re

from pyramid.url import resource_url
from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_root, find_interface
from repoze.folder.interfaces import IObjectAddedEvent
from webhelpers.html.converters import nl2br

from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core.models.user import userid_regexp

def urls_to_links(text):
    reg = re.compile(r"(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)")
    text = reg.sub(r'<a href="\1">\1</a>', text)
    
    return text

def at_userid_link(text, obj):
    root = find_root(obj)
    meeting = find_interface(obj, IMeeting)
    users = root.users
    request = get_current_request()

    regexp = r'(\A|\s)@('+userid_regexp+r')'
    reg = re.compile(regexp)
    for (space, userid) in re.findall(regexp, text):
        if userid in users:
            user = users[userid]
            link = '%s<a href="%s_userinfo?userid=%s" title="%s" class="inlineinfo">%s</a>' % (
                space,
                resource_url(meeting, request),
                userid,
                user.title,
                userid,
            )
            user.send_mention_notification(obj, request)
            text = text.replace(space+'@'+userid, link)
    
    return text

@subscriber([IProposal, IObjectAddedEvent])
def transform_title(obj, event):
    text = obj.get_field_value('title')

    # nl2br returns an object that automagicaly escapes html, so we converts it to a unicode string
    text = unicode(nl2br(text))
    text = urls_to_links(text)
    text = at_userid_link(text, obj)

    obj.set_field_value('title', text)

@subscriber([IDiscussionPost, IObjectAddedEvent])
def transform_text(obj, event):
    text = obj.get_field_value('text')

    # nl2br returns an object that automagicaly escapes html, so we converts it to a unicode string
    text = unicode(nl2br(text))
    text = urls_to_links(text)
    text = at_userid_link(text, obj)

    obj.set_field_value('text', text)
