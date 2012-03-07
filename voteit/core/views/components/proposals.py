from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource

from voteit.core import VoteITMF as _
from voteit.core.security import RETRACT
from voteit.core.models.proposal import Proposal


@view_action('proposals', 'listing')
def proposal_listing(context, request, va, **kw):
    """ Get proposals for a specific context """
    api = kw['api']

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
                return _(info['title']) 
        
        return state

    response = {}
    response['proposals'] = api.get_metadata_for_query(content_type = 'Proposal',
                                                       sort_index = 'created',
                                                       path = resource_path(context))
    response['api'] = api
    response['show_retract'] = _show_retract
    response['translated_state_title'] = _translated_state_title 
    return render('../templates/proposals.pt', response, request = request)
