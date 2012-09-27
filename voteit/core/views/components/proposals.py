from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from repoze.catalog.query import NotAny
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
        
        def _notify_delete(uids):
            # check if there is proposals in locked for voteing, approved or deniyed
            query = Eq('path', resource_path(context)) & \
                    Eq('content_type', 'Proposal') & \
                    Any('workflow_state', ('voting', 'approved', 'denied')) & \
                    Any('uid', uids)
        
            if api.root.catalog.query(query)[0] > 0:
                return 'notify_delete' 
            else: 
                return ''
        
        response = {}
        response['api'] = api
        response['polls'] = polls
        response['get_proposal_brains'] = _get_proposal_brains
        response['notify_delete'] = _notify_delete
        return render('../templates/polls.pt', response, request=request)
    
    polls = api.get_restricted_content(context, iface=IPoll, sort_on='created')
    for poll in polls:
        try:
            plugin = poll.get_poll_plugin()
        except ComponentLookupError:
            err_msg = _(u"plugin_missing_error",
                        default = u"Can't find any poll plugin with name '${name}'. Perhaps that package has been uninstalled?",
                        mapping = {'name': poll.get_field_value('poll_plugin')})
            api.flash_messages.add(err_msg, type="error")
            continue
        
    uids = set()
    for poll in polls:
        uids.update(poll.proposal_uids)
    
    query = Eq('path', resource_path(context)) & \
            Eq('content_type', 'Proposal') & \
            (NotAny('uid', uids) | \
            Any('workflow_state', ('published', 'retracted', 'unhandled')))
    
    total_count = api.root.catalog.query(query)[0]
    
    tag = request.GET.get('tag', None)
    if tag:
        query = query & Any('tags', (tag, ))
        
    # build query string and remove tag
    clear_tag_query = request.GET.copy()
    if 'tag' in clear_tag_query:
        del clear_tag_query['tag']
        
    count, docids = api.root.catalog.query(query, sort_index='created', reverse=True)
    get_metadata = api.root.catalog.document_map.get_metadata
    results = []
    for docid in docids:
        #Insert the resolved docid first, since we need to reverse order again.
        results.insert(0, get_metadata(docid))

    response = {}
    response['get_polls'] = _get_polls
    response['polls'] = polls
    response['clear_tag_url'] = api.request.resource_url(context, query=clear_tag_query)
    response['proposals'] = tuple(results)
    response['hidden_count'] = total_count - count
    response['api'] = api 
    return render('../templates/proposals.pt', response, request = request)

@view_action('proposal', 'block')
def proposal_block(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']
    show_user_tags = kw.get('show_user_tags', True)
    
    # crearting dummy proposal to get state info dict
    state_info = _dummy_proposal.workflow.state_info(None, request)
    
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

_dummy_proposal = Proposal()
