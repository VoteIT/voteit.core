from betahaus.viewcomponent import view_action
from betahaus.viewcomponent.interfaces import IViewGroup
from pyramid.renderers import render
from pyramid.security import effective_principals
from pyramid.traversal import resource_path
from repoze.catalog.query import Eq
from repoze.catalog.query import Any

from voteit.core import VoteITMF as _


@view_action('main', 'tag_stats')
def tag_stats(context, request, *args, **kwargs):
    api = kwargs['api']

    if not api.meeting:
        return ""
    
    workflow_state = ('published', 'unhandled', 'voting', 'approved', 'denied',)
    if api.meeting.get_field_value('show_retracted', True) or request.GET.get('show_retracted') == '1':
        workflow_state = ('published', 'retracted', 'unhandled', 'voting', 'approved', 'denied',)
    
    query = Eq('path', resource_path(context)) & \
            Any('allowed_to_view', effective_principals(request)) & \
            (Eq('content_type', 'Proposal') & Any('workflow_state', workflow_state) | \
             Eq('content_type', 'DiscussionPost'))

    num, docids = api.root.catalog.query(query)
    stats = {}
    for docid in docids:
        entrie = api.root.catalog.document_map.get_metadata(docid)
        for tag in entrie['tags']:
            if not tag in stats:
                stats[tag] = 1
            else:
                stats[tag] = stats[tag] + 1
     
    query = query & Eq('unread', api.userid)
    num, docids = api.root.catalog.query(query)
    unread = {}
    for docid in docids:
        entrie = api.root.catalog.document_map.get_metadata(docid)
        for tag in entrie['tags']:
            if not tag in unread:
                unread[tag] = 1
            else:
                unread[tag] = unread[tag] + 1
                
    def _make_url(tag):
        query = request.GET.copy()
        query['tag'] = tag
        return request.resource_url(context, '', query=query)
    
    response = dict(
        api = api,
        context = context,
        stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:5],
        unread = unread,
        make_url = _make_url,
    )

    return render('../templates/snippets/tag_stats.pt', response, request = request)