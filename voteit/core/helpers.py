import re

from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_root
from pyramid.traversal import find_interface
from pyramid.url import resource_url
from webhelpers.html import HTML
from slugify import slugify

from voteit.core.models.interfaces import IMeeting


ajax_options = """
{success: voteit_deform_success,
}
"""

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
        # The pattern contains a space so we only find usernames that 
        # has a whitespace in front, we save the spaced so we can but 
        # it back after the transformation
        space, userid = matchobj.group(1, 2)
        #Force lowercase userid
        userid = userid.lower()
        user = users[userid]
        user.send_mention_notification(obj, request)

        tag = {}
        tag['href'] = "%s_userinfo?userid=%s" % (resource_url(meeting, request), userid)
        tag['title'] = user.title
        tag['class'] = "inlineinfo"
        return space + HTML.a('@%s' % userid, **tag)

    return re.sub(AT_PATTERN, handle_match, text)
    

def generate_slug(context, text, limit=40):
    """ Suggest a name for content that will be added.
        text is a title or similar to be used.
    """
    suggestion = slugify(text[:limit])
    
    #Is the suggested ID already unique?
    if suggestion not in context:
        return suggestion
    
    #ID isn't unique, let's try to generate a unique one.
    RETRY = 100
    i = 1
    while i <= RETRY:
        new_s = "%s-%s" % (suggestion, str(i))
        if new_s not in context:
            return new_s
        i += 1
    #If no id was found, don't just continue
    raise KeyError("No unique id could be found")