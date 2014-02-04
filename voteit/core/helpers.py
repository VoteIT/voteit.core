import re
from copy import deepcopy

from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_root
from pyramid.traversal import find_interface
from pyramid.i18n import get_localizer
from pyramid.i18n import TranslationString
from webhelpers.html import HTML
from webhelpers.html.render import sanitize
from webhelpers.html.converters import nl2br
from betahaus.pyracont import generate_slug #For b/c, please keep this until cleared!
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from html2text import HTML2Text

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem


ajax_options = """
{success: voteit_deform_success,
}
"""

AT_PATTERN = re.compile(r'(\A|\s)@([a-zA-Z1-9]{1}[\w-]+)', flags=re.UNICODE)
TAG_PATTERN = re.compile(r'(\A|\s|[,.;:!?])#(?P<tag>\w*[\w-]+)(\w*)', flags=re.UNICODE)
#TAG_PATTERN = re.compile(r'(\A|\s|[,.;:!?])#(?P<tag>\w+)', flags=re.UNICODE)


def at_userid_link(text, obj, request=None):
    """ Transform @userid to a link.
    """
    users = find_root(obj).users
    meeting = find_interface(obj, IMeeting)
    assert meeting
    if not request:
        request = get_current_request()

    def handle_match(matchobj):
        # The pattern contains a space so we only find usernames that 
        # has a whitespace in front, we save the spaced so we can but 
        # it back after the transformation
        space, userid = matchobj.group(1, 2)
        #Force lowercase userid
        userid = userid.lower()
        if userid in users: 
            user = users[userid]
    
            tag = {}
            tag['href'] = request.resource_url(meeting, '_userinfo', query={'userid': userid}).replace(request.application_url, '')
            tag['title'] = user.title
            tag['class'] = "inlineinfo"
            return space + HTML.a('@%s' % userid, **tag)
        else:
            return space + '@' + userid

    return re.sub(AT_PATTERN, handle_match, text)


def tags2links(text, api):
    """ Transform #tag to a link.
    """
    #FIXME: Breaks outside of ais? Ehh?
    ai = find_interface(api.context, IAgendaItem)
    def handle_match(matchobj):
        pre, tag, post = matchobj.group(1, 2, 3)
        link = {'href': api.request.resource_url(ai, '', query={'tag': tag}).replace(api.request.application_url, ''),
                'class': "tag",}
        return """%(pre)s%(link)s%(post)s""" % {'pre': pre, 'link': HTML.a('#%s' % tag, **link), 'post': post}
    return re.sub(TAG_PATTERN, handle_match, text)

def strip_and_truncate(text, limit=200):
    try:
        text = sanitize(text)
    except Exception, e:
        #FIXME: Logg unrecoverable error
        #This is a bad exception that should never happen, if we translate it it will be hard to search in the source code
        return u"Unrecoverable error: could not truncate text"
    if len(text) > limit:
        text = u"%s<...>" % nl2br(text[:limit])
    return nl2br(text)

def move_object(obj, new_parent):
    """ Move an object to a new location. """
    name = obj.__name__
    if name in new_parent:
        raise ValueError("Already exist")
    old_parent = obj.__parent__
    new_obj = deepcopy(obj)
    del old_parent[name]
    new_parent[name] = new_obj
    return new_obj

def send_email(subject, recipients, html, sender = None, plaintext = None, request = None, send_immediately = False, **kw):
    """ Send an email to users. This also checks the required settings and translates
        the subject.
        
        returns the message object sent, or None
    """ #FIXME: Docs
    if request is None:
        request = get_current_request()
    localizer = get_localizer(request)
    if isinstance(subject, TranslationString):
        subject = localizer.translate(subject)
    if isinstance(recipients, basestring):
        recipients = (recipients,)
    assert isinstance(html, basestring)
    if plaintext is None:
        html2text = HTML2Text()
        html2text.ignore_links = True
        html2text.ignore_images = True
        html2text.body_width = 0
        plaintext = html2text.handle(html).strip()
    if not plaintext:
        plaintext = None #In case it was an empty string
    #It seems okay to leave sender blank since it's part of the default configuration
    msg = Message(subject = subject,
                  recipients = recipients,
                  sender = sender,
                  body = plaintext,
                  html = html,
                  **kw)
    mailer = get_mailer(request)
    #Note that messages are sent during the transaction process. See pyramid_mailer docs
    if send_immediately:
        mailer.send_immediately(msg)
    else:
        mailer.send(msg)
    return msg
    #FIXME: Add logger
