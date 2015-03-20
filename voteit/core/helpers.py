import re
from copy import deepcopy
from urllib import urlencode

from pyramid.renderers import render
from pyramid.traversal import find_interface
from repoze.workflow import get_workflow
from webhelpers.html.converters import nl2br
from webhelpers.html.render import sanitize
from webhelpers.html.tools import auto_link
from arche.utils import generate_slug #API

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core import security


ajax_options = """
{success: voteit_deform_success,
}
"""

AT_PATTERN = re.compile(r'(\A|\s)@([a-zA-Z1-9]{1}[\w-]+)', flags=re.UNICODE)
TAG_PATTERN = re.compile(r'(?P<pre>\A|\s|[,.;:!?])#(?P<tag>\w*[\w-]+)', flags=re.UNICODE)


def at_userid_link(request, text):
    """ Transform @userid to a link.
    """
    #users = find_root(obj).users
    meeting = request.meeting #find_interface(obj, IMeeting)
    assert meeting
    def handle_match(matchobj):
        # The pattern contains a space so we only find usernames that 
        # has a whitespace in front, we save the spaced so we can but 
        # it back after the transformation
        #space, userid = matchobj.group(1, 2)
        userid = matchobj.group(2)
        #Force lowercase userid
        userid = userid.lower()
        return " %s" % request.creators_info([userid], lookup = False, at = True)
        
#         if userid in users: 
#             user = users[userid]
#     
#             tag = {}
#             tag['href'] = request.resource_url(meeting, '_userinfo', query={'userid': userid}).replace(request.application_url, '')
#             tag['title'] = user.title
#             tag['class'] = "inlineinfo"
#             return space + HTML.a('@%s' % userid, **tag)
#         else:
#             return space + '@' + userid

    return re.sub(AT_PATTERN, handle_match, text)


def tags2links(text):
    """ Transform #tag to a relative link in this context.
        Not domain name or path will be included - it starts with './'
    """
    def handle_match(matchobj):
        matched_dict = matchobj.groupdict()
        tag = matched_dict['tag']
        pre = matched_dict['pre']
        url = u"?%s" % urlencode({'tag': tag.encode('utf-8')})
        return u"""%(pre)s<a href="%(url)s" data-set-tag-filter="%(tag)s" class="tag">#%(tag)s</a>""" % {'pre': pre, 'url': url, 'tag': tag}
    return re.sub(TAG_PATTERN, handle_match, text)

def strip_and_truncate(text, limit=200, symbol = '<span class="trunc">&hellip;</span>'):
    try:
        text = sanitize(text)
    except Exception, e:
        #FIXME: Logg unrecoverable error
        #This is a bad exception that should never happen
        return u"Unrecoverable error: could not truncate text"
    out = ""
    pool = text
    while pool and len(out) < limit:
        word, pool = pool.partition(' ')[0::2]
        out += word + ' '
    out = out.strip()
    if pool:
        out += symbol
    return  out

#     if len(text) > limit:
#         text = u"%s<...>" % nl2br(text[:limit])
#     return nl2br(text)

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

def transform_text(request, text):
    text = sanitize(text)
    #text = auto_link(text, link='urls')
    text = auto_link(text)
    text = nl2br(text)
    text = tags2links(unicode(text))
    text = at_userid_link(request, text)
    return text

def creators_info(request, creators, portrait = True, lookup = True, at = False):
    if lookup == False:
        portrait = False #No portrait without lookup
    users = []
    for userid in creators:
        if lookup:
            user = request.root['users'].get(userid, None)
            if user:
                users.append(user)
        else:
            users.append(userid)
    response = {'users': users, 'portrait': portrait, 'lookup': lookup, 'at': at}
    return render('voteit.core:templates/snippets/creators_info.pt', response, request = request)

def get_meeting(request):
    return find_interface(request.context, IMeeting)

def get_ai(request):
    return find_interface(request.context, IAgendaItem)

def get_userinfo_url(request, userid):
    return request.resource_url(request.meeting, '__userinfo__', userid)

def is_moderator(request):
    return request.has_permission(security.MODERATE_MEETING, request.meeting)

def get_wf_state_titles(request, iface, type_name):
    wf = get_workflow(iface, type_name)
    results = {}
    for sinfo in wf.state_info(None, request):
        results[sinfo['name']] = request.localizer.translate(sinfo['title'], domain = 'voteit.core')
    return results

def tags_from_text(text):
    tags = []
    for matchobj in re.finditer(TAG_PATTERN, text):
        tag = matchobj.group('tag').lower()
        if tag not in tags:
            tags.append(tag)
    return tags

def get_at_userids(text):
    results = set()
    for matchobj in re.finditer(AT_PATTERN, text):
        userid = matchobj.group(2)
        #Force lowercase userid
        userid = userid.lower()
        results.add(userid)
    return results

def get_meeting_participants(meeting):
    """ Return all userids who're part of this meeting.
        This should be cached later on.
    """
    return security.find_authorized_userids(meeting, [security.VIEW])

def includeme(config):
    config.add_request_method(callable = transform_text, name = 'transform_text')
    #Hook creators info
    config.add_request_method(callable = creators_info, name = 'creators_info')
    #Hook meeting & agenda item
    config.add_request_method(callable = get_meeting, name = 'meeting', reify = True)
    config.add_request_method(callable = get_ai, name = 'agenda_item', reify = True)
    #Userinfo URL
    config.add_request_method(callable = get_userinfo_url, name = 'get_userinfo_url')
    #Is moderator
    config.add_request_method(callable = is_moderator, name = 'is_moderator', reify = True)
    #State titles
    config.add_request_method(callable = get_wf_state_titles, name = 'get_wf_state_titles')
