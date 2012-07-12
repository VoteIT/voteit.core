from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource
from repoze.catalog.query import Any

from voteit.core import VoteITMF as _
from voteit.core.security import RETRACT
from voteit.core.models.interfaces import IPoll
from voteit.core.models.proposal import Proposal


@view_action('proposals', 'listing')
def proposal_listing(context, request, va, **kw):
    """ Get proposals for a specific context """
    api = kw['api']

    response = {}
    
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
    
    response['proposals'] = api.get_metadata_for_query(content_type = 'Proposal',
                                                       sort_index = 'created',
                                                       path = resource_path(context))
    response['api'] = api 
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