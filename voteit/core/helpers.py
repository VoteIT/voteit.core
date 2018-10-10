import re
from logging import getLogger
from urllib import urlencode

from arche.utils import generate_slug #API
from pyramid.renderers import render
from pyramid.traversal import find_interface
from pyramid.traversal import resource_path
from redis import StrictRedis
from repoze.catalog.query import Any, NotAny
from repoze.catalog.query import Eq
from repoze.workflow import get_workflow
from webhelpers.html.converters import nl2br
from webhelpers.html.tools import strip_tags
from webhelpers.html.tools import auto_link

from voteit.core import _
from voteit.core import security
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiffText
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IMeeting


ajax_options = """
{success: voteit_deform_success,
}
"""

AT_PATTERN = re.compile(r'(\A|\s)@([a-zA-Z1-9]{1}[\w-]+)', flags=re.UNICODE)
TAG_PATTERN = re.compile(r'(?P<pre>\A|\s|[,.;:!?])#(?P<tag>\w*[\w-]+)', flags=re.UNICODE)

ROLE_ICONS = {
    security.ROLE_VIEWER: 'glyphicon glyphicon-eye-open',
    security.ROLE_DISCUSS: 'glyphicon glyphicon-comment',
    security.ROLE_PROPOSE: 'glyphicon glyphicon-exclamation-sign',
    security.ROLE_VOTER: 'glyphicon glyphicon-star',
    security.ROLE_MODERATOR: 'glyphicon glyphicon-king',
    security.ROLE_ADMIN: 'glyphicon glyphicon-cog'
}


def at_userid_link(request, text):
    """ Transform @userid to a link.
    """
    meeting = request.meeting
    assert meeting

    def handle_match(matchobj):
        # The pattern contains a space so we only find usernames that 
        # has a whitespace in front, we save the spaced so we can but 
        # it back after the transformation
        # space, userid = matchobj.group(1, 2)
        userid = matchobj.group(2)
        # Force lowercase userid
        userid = userid.lower()
        return " %s" % request.creators_info([userid], lookup=False, at=True)

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
        # FIXME: data-ai-name="${context.__name__}
        # This should be refactored and handled through javascript
        return u"""%(pre)s<a href="%(url)s" data-load-agenda-item="#content" class="tag">#%(tag)s</a>""" % \
               {'pre': pre, 'url': url, 'tag': tag}

    return re.sub(TAG_PATTERN, handle_match, text)


def strip_and_truncate(text, limit=200, symbol='<span class="trunc">&hellip;</span>'):
    try:
        text = strip_tags(text)
    except Exception, e:
        # FIXME: Logg unrecoverable error
        # This is a bad exception that should never happen
        return u"Unrecoverable error: could not truncate text"
    out = ""
    pool = text
    while pool and len(out) < limit:
        word, pool = pool.partition(' ')[0::2]
        out += word + ' '
    out = out.strip()
    if pool:
        out += symbol
    return out


def transform_text(request, text, html=True, tag_func=tags2links):
    if html:
        text = auto_link(text)
        text = nl2br(text)
        text = tag_func(unicode(text))
        text = at_userid_link(request, text)
    return text


def creators_info(request, creators, portrait=True, lookup=True, at=False, no_tag=False,
                  no_userid=False):
    if lookup == False:
        portrait = False  # No portrait without lookup
    users = []
    for userid in creators:
        if lookup:
            user = request.root['users'].get(userid, None)
            if user:
                users.append(user)
        else:
            users.append(userid)
    response = {'users': users,
                'portrait': portrait,
                'lookup': lookup,
                'at': at,
                'no_tag': no_tag,
                'no_userid': no_userid}
    return render('voteit.core:templates/snippets/creators_info.pt', response, request=request)


def get_meeting(request):
    try:
        return find_interface(request.context, IMeeting)
    except AttributeError:
        pass


def get_ai(request):
    try:
        return find_interface(request.context, IAgendaItem)
    except AttributeError:
        pass


def get_userinfo_url(request, userid):
    return request.resource_url(request.meeting, '__userinfo__', userid)


def is_moderator(request):
    """ Request method to determine if someone is a moderator. Also true for admins in the root.
    """
    try:
        if request.meeting:
            return request.has_permission(security.MODERATE_MEETING, request.meeting)
        else:
            return request.has_permission(security.MANAGE_SERVER, request.root)
    except AttributeError:
        pass


def is_participant(request):
    try:
        return request.meeting and request.has_permission(security.VIEW, request.meeting)
    except AttributeError:
        pass


def get_wf_state_titles(request, iface, type_name):
    wf = get_workflow(iface, type_name)
    results = {}
    tstring = _
    for sinfo in wf.state_info(None, request):
        results[sinfo['name']] = request.localizer.translate(tstring(sinfo['title']))
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
        # Force lowercase userid
        userid = userid.lower()
        results.add(userid)
    return results


def get_meeting_participants(meeting):
    """ Return all userids who're part of this meeting.
        This should be cached later on.
    """
    return security.find_authorized_userids(meeting, [security.VIEW])


def get_docids_to_show(request, context, type_name, tags=(), limit=5, start_after=None,
                       end_before=None):
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
    assert IAgendaItem.providedBy(context)
    query = Eq('path', resource_path(context))
    query &= Eq('type_name', type_name)
    if tags:
        query &= Any('tags', list(tags))
    read_names = request.get_read_names(context)
    unread_query = query & NotAny('__name__', set(read_names.get(request.authenticated_userid, [])))
    unread_docids = list(request.root.catalog.query(unread_query, sort_index='created')[1])
    docids_pool = list(request.root.catalog.query(query, sort_index='created')[1])

    if start_after and start_after in docids_pool:
        i = docids_pool.index(start_after)
        for docid in docids_pool[:i + 1]:
            if docid in unread_docids:
                unread_docids.remove(docid)
        docids_pool[0:i + 1] = []
    if end_before and end_before in docids_pool:
        i = docids_pool.index(end_before)
        for docid in docids_pool[i:]:
            if docid in unread_docids:
                unread_docids.remove(docid)
        docids_pool[i:] = []
    if limit:
        if unread_docids:
            first_pos = docids_pool.index(unread_docids[0])
            batch = docids_pool[first_pos:first_pos + limit]
            over_limit = docids_pool[first_pos + limit:]
            previous = docids_pool[:first_pos]
            # Fill batch from last item of previous if batch is too small
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
    # no limit
    return {'batch': docids_pool,
            'previous': [],
            'over_limit': [],
            'unread': unread_docids}


def get_polls_struct(meeting, request, limit=5):
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
        # Note: Sorted items
        res, docids = request.root.catalog.query(squery, **state_query[state])
        result = {}
        result['over_limit'] = res.total - res.real
        result['docids'] = docids  # To allow caching or skip resolving polls
        result['polls'] = request.resolve_docids(docids)
        result['state'] = state
        results.append(result)
    return results


def clear_tags_url(request, context, *args, **kw):
    clear_tag_query = request.GET.copy()
    if 'tag' in clear_tag_query:
        del clear_tag_query['tag']
    clear_tag_query.update(kw)
    return request.resource_url(context, *args, query=clear_tag_query)


def render_proposal_text(request, proposal, tag_func=tags2links):
    """ Render a proposal as a diff or as the original text. """
    if not IProposal.providedBy(proposal):
        raise TypeError("%s is not a proposal" % proposal)
    if proposal.diff_text_para is None:
        #This is a regular proposal without the diff functions active
        return request.transform_text(proposal.text, tag_func=tag_func)
    else:
        ai = request.agenda_item
        if ai is None:
            ai = proposal.__parent__
        diff_text = IDiffText(ai)
        paragraphs = diff_text.get_paragraphs()
        try:
            original = paragraphs[proposal.diff_text_para]
        except (TypeError, IndexError):
            #Simply abort
            return request.transform_text(proposal.text, tag_func=tag_func)
        text = ""
        if proposal.diff_text_leadin:
            text += tag_func(proposal.diff_text_leadin) + "\n\n"
        text += diff_text(original, proposal.text, brief=True)
        return nl2br(text).unescape()


def redis_conn(request):
    return StrictRedis.from_url(request.registry.settings['voteit.redis_url'])


def _configure_fake_redis(config):
    try:
        from fakeredis import FakeStrictRedis
    except ImportError:
        raise ImportError("fakeredis not found, install with voteit.core[testing]")
    def _testing_redis_conn(reqest):
        return FakeStrictRedis()
    config.add_request_method(_testing_redis_conn, name='redis_conn', reify=True)


def includeme(config):
    logger = getLogger(__name__)
    config.add_request_method(get_docids_to_show)
    config.add_request_method(callable=transform_text, name='transform_text')
    # Hook creators info
    config.add_request_method(callable=creators_info, name='creators_info')
    # Hook meeting & agenda item
    config.add_request_method(callable=get_meeting, name='meeting', reify=True)
    config.add_request_method(callable=get_ai, name='agenda_item', reify=True)
    # Userinfo URL
    config.add_request_method(callable=get_userinfo_url, name='get_userinfo_url')
    # Is moderator
    config.add_request_method(callable=is_moderator, name='is_moderator', reify=True)
    config.add_request_method(callable=is_participant, name='is_participant', reify=True)
    # State titles
    config.add_request_method(callable=get_wf_state_titles, name='get_wf_state_titles')
    config.add_request_method(callable=clear_tags_url)
    # Special rendering for proposal
    config.add_request_method(render_proposal_text)
    # Redis connection
    settings = config.registry.settings
    # Allow fake redis if the testrunner is running this, or if this is a debug-enabled instance
    # without configuration
    if config.registry.package_name == 'testing':
        _configure_fake_redis(config)
    elif (not settings.get('voteit.redis_url', False) and settings.get('arche.debug', False)):
        logger.warn("'voteit.redis_url' is missing in config. "
                    "Will run with FakeRedis, so nothing will be stored!")
        _configure_fake_redis(config)
    else:
        assert 'voteit.redis_url' in settings, "'voteit.redis_url' is required in settings"
        config.add_request_method(redis_conn, reify=True)
