import re
from copy import deepcopy
from urllib import urlencode

from arche.utils import generate_slug #API
from pyramid.renderers import render
from pyramid.traversal import find_interface
from pyramid.traversal import resource_path
from repoze.workflow import get_workflow
from webhelpers.html.converters import nl2br
from webhelpers.html.render import sanitize
from webhelpers.html.tools import auto_link

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
    """ Request method to determine if someone is a moderator. Also true for admins in the root.
    """
    if request.meeting:
        return request.has_permission(security.MODERATE_MEETING, request.meeting)
    else:
        return request.has_permission(security.MANAGE_SERVER, request.root)

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

def get_docids_to_show(context, request, type_name, tags = (), limit = 5, start_after = None, end_before = None):
    """ Helper method to fetch docids that would be a resonable batch to show.
        This is mostly to allow agenda views to load fast.

        - Fetch batch from the first unread docid so there will be no items
            skipped in case they were read from a tag view.
        - If batch contains less items than limit, insert items from previous.
        - start_after - remove everything before this docid and the value specified.
        - end_before - remove this value and everything after it.
        
        Result example:
        {'batch': [4, 5, 6], 'previous': [1, 2, 3], 'over_limit': [7, 8, 9], 'unread': [4, 5, 6, 7, 8, 9]}
    """
    query = "path == '%s' and type_name == '%s'" % (resource_path(context), type_name)
    if tags:
        query += " and tags in any(%s)" % list(tags)
    unread_query = "unread == '%s' and %s" % (request.authenticated_userid, query)
    catalog_query = request.root.catalog.query
    unread_docids = list(catalog_query(unread_query, sort_index = 'created')[1])
    docids_pool = list(catalog_query(query, sort_index = 'created')[1])
    if start_after and start_after in docids_pool:
        i = docids_pool.index(start_after)
        for docid in docids_pool[:i+1]:
            if docid in unread_docids:
                unread_docids.remove(docid)
        docids_pool[0:i+1] = []
    if end_before and end_before in docids_pool:
        i = docids_pool.index(end_before)
        for docid in docids_pool[i:]:
            if docid in unread_docids:
                unread_docids.remove(docid)
        docids_pool[i:] = []
    if limit:
        if unread_docids:
            first_pos = docids_pool.index(unread_docids[0])
            batch = docids_pool[first_pos:first_pos+limit]
            over_limit = docids_pool[first_pos+limit:]
            previous = docids_pool[:first_pos]
            #Fill batch from last item of previous if batch is too small
            while previous and len(batch) < limit:
                batch.insert(0, previous.pop(-1))
        else:
            batch = docids_pool[-limit:]
            previous = docids_pool[:-limit]
            over_limit = []
        return {'batch': batch,
                'previous': previous,
                'over_limit': over_limit,
                'unread': unread_docids}
    #no limit
    return {'batch': docids_pool,
            'previous': [],
            'over_limit': [],
            'unread': unread_docids}

def get_polls_struct(meeting, request, limit = 5):
    """ Return a dict with polls sorted according to workflow states and some metadata about the result."""
    states = ['ongoing', 'upcoming', 'closed']
    state_query = {'ongoing': {'sort_index': 'start_time', 'reverse': True},
                   'upcoming': {'sort_index': 'created', 'limit': limit},
                   'closed': {'sort_index': 'end_time', 'reverse': True, 'limit': limit},
                   'private': {'sort_index': 'created', 'limit': limit}}
    if request.is_moderator:
        states.append('private')
    query = "type_name == 'Poll' and path == '%s'" % resource_path(meeting)
    results = []
    for state in states:
        squery = "%s and workflow_state == '%s'" % (query, state)
        #Note: Sorted items
        res, docids = request.root.catalog.query(squery, **state_query[state])
        result = {}
        result['over_limit'] = res.total - res.real
        result['docids'] = docids #To allow caching or skip resolving polls
        result['polls'] = request.resolve_docids(docids)
        result['state'] = state
        results.append(result)
    return results

def current_tags(request, prepend = '#', separator = ', '):
    return separator.join(["%s%s" % (prepend, x) for x in request.GET.getall('tag')])

def clear_tags_url(request, context, *args, **kw):
    clear_tag_query = request.GET.copy()
    if 'tag' in clear_tag_query:
        del clear_tag_query['tag']
    clear_tag_query.update(kw)
    return request.resource_url(context, *args, query = clear_tag_query)

def includeme(config):
    #FIXME: What's a good test for request methods? They aren't included during the regular testing runs.
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
    config.add_request_method(callable = current_tags)
    config.add_request_method(callable = clear_tags_url)
