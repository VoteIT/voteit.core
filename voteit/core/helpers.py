import re

from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_root
from pyramid.traversal import find_interface
from pyramid.url import resource_url
from webhelpers.html import HTML

from voteit.core.models.interfaces import IMeeting


AT_PATTERN = re.compile(r'(\A|\s)@([a-zA-Z1-9]{1}[\w-]{1,14})')

def at_userid_link(text, obj):
    """ Transform @userid to a link.
        Only use this method on write.
        Will send notification if user profile can be found.
        When this method is run, validation will already have taken place.
    """
    users = find_root(obj).users
    meeting = find_interface(obj, IMeeting)
    assert meeting
    request = get_current_request()

    def handle_match(matchobj):
        #FIXME: Space? :)
        space, userid = matchobj.group(1, 2)
        user = users[userid]
        user.send_mention_notification(obj, request)

        tag = {}
        tag['href'] = "%s_userinfo?userid=%s" % (resource_url(meeting, request), userid)
        tag['title'] = user.title
        tag['class'] = "inlineinfo"
        return space + HTML.a('@%s' % userid, **tag)

    return re.sub(AT_PATTERN, handle_match, text)
