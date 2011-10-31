# -*- coding: utf-8 -*-

import re

from pyramid.url import resource_url
from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_root, find_interface
from repoze.folder.interfaces import IObjectAddedEvent
from webhelpers.html.converters import nl2br
from webhelpers.html.tools import auto_link
from webhelpers.html import HTML

from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core.models.user import USERID_REGEXP

#FIXME: This could be custom accessors on Proposal / DiscussionPost

def urls_to_links(text):
    return auto_link(text, link='urls')

def at_userid_link(text, obj):
    root = find_root(obj)
    meeting = find_interface(obj, IMeeting)
    users = root.users
    request = get_current_request()

    regexp = r'(\A|\s)@('+USERID_REGEXP+r')'
    def handle_match(matchobj):
        all = matchobj.group()
        space, userid = matchobj.group(1, 2)
        if userid in users:
            user = users[userid]
            user.send_mention_notification(obj, request)
            a_options = dict()
            a_options['href'] = "%s_userinfo?userid=%s" % (resource_url(meeting, request), userid)
            a_options['title'] = user.title
            a_options['class'] = "inlineinfo"
            return HTML.a('@'+userid, **a_options)
        else:
            return space+'@'+userid
            
    return re.sub(regexp, handle_match, text)

@subscriber([IProposal, IObjectAddedEvent])
def transform_title(obj, event):
    text = obj.get_field_value('title')

    text = urls_to_links(text)
    text = at_userid_link(text, obj)
    text = nl2br(text)
    
    obj.set_field_value('title', text)

@subscriber([IDiscussionPost, IObjectAddedEvent])
def transform_text(obj, event):
    text = obj.get_field_value('text')

    text = urls_to_links(text)
    text = at_userid_link(text, obj)
    text = nl2br(text)

    obj.set_field_value('text', text)
