from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource
from repoze.catalog.query import Any
from zope.component.interfaces import ComponentLookupError

from voteit.core import VoteITMF as _
from voteit.core.security import RETRACT
from voteit.core.models.interfaces import IPoll
from voteit.core.models.proposal import Proposal


@view_action('proposals', 'listing')
def proposal_listing(context, request, va, **kw):
    """ Get proposals for a specific context """
    api = kw['api']
    
    def _get_polls(polls):
        
        def _get_proposal_brains(uids):
            query = api.root.catalog.query
            get_metadata = api.root.catalog.document_map.get_metadata
            
            num, results = query(Any('uid', uids), sort_index = 'created')
            return [get_metadata(x) for x in results]
        
        response = {}
        response['api'] = api
        response['polls'] = polls
        response['get_proposal_brains'] = _get_proposal_brains
        return render('../templates/polls.pt', response, request=request)

    def _show_retract(brain):
        #Do more expensive checks last!
        if brain['workflow_state'] != 'published':
            return
        if not api.userid in brain['creators']:
            return
        #Now for the 'expensive' stuff
        obj = find_resource(api.root, brain['path'])
        return api.context_has_permission(RETRACT, obj)
    
    # crearting dummy proposal to get state info dict
    state_info = Proposal().workflow.state_info(None, request)
    
    def _translated_state_title(state):
        for info in state_info:
            if info['name'] == state:
                return api.tstring(info['title'])
        
        return state
    
    query = dict(content_type = 'Proposal',
                 sort_index = 'created',
                 reverse = True,
                 path = resource_path(context))
    
    total_count = api.search_catalog(**query)[0]
    
    tag = request.GET.get('tag', None)
    if tag:
        query['tags'] = tag
        
    # build query string and remove tag=
    clear_tag_query = request.GET.copy()
    if 'tag' in clear_tag_query:
        del clear_tag_query['tag']
        
    count, docids = api.search_catalog(**query)
    get_metadata = api.root.catalog.document_map.get_metadata
    results = []
    for docid in docids:
        #Insert the resolved docid first, since we need to reverse order again.
        results.insert(0, get_metadata(docid))

    response = {}
    response['get_polls'] = _get_polls
    response['polls'] = api.get_restricted_content(context, iface=IPoll, sort_on='created')
    for poll in response['polls']:
        try:
            plugin = poll.get_poll_plugin()
        except ComponentLookupError:
            err_msg = _(u"plugin_missing_error",
                        default = u"Can't find any poll plugin with name '${name}'. Perhaps that package has been uninstalled?",
                        mapping = {'name': poll.get_field_value('poll_plugin')})
            api.flash_messages.add(err_msg, type="error")
            continue
    response['clear_tag_url'] = api.request.resource_url(context, query=clear_tag_query)
    response['proposals'] = tuple(results)
    response['hidden_count'] = total_count - count
    response['api'] = api
    response['show_retract'] = _show_retract
    response['translated_state_title'] = _translated_state_title 
    return render('../templates/proposals.pt', response, request = request)

@view_action('proposal', 'block')
def proposal_block(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']
    show_user_tags = kw.get('show_user_tags', True)
    
    # crearting dummy proposal to get state info dict
    state_info = Proposal().workflow.state_info(None, request)
    
    def _show_retract(brain):
        #Do more expensive checks last!
        if brain['workflow_state'] != 'published':
            return
        if not api.userid in brain['creators']:
            return
        #Now for the 'expensive' stuff
        obj = find_resource(api.root, brain['path'])
        return api.context_has_permission(RETRACT, obj)
    
    def _translated_state_title(state):
        for info in state_info:
            if info['name'] == state:
                return api.tstring(info['title'])
        
        return state
    
    response = {}
    response['api'] = api
    response['brain'] = brain
    response['translated_state_title'] = _translated_state_title
    response['show_retract'] = _show_retract
    response['show_user_tags'] = show_user_tags
    
    return render('../templates/proposal.pt', response, request=request)
