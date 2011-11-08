from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path, find_resource

from deform import Form
from voteit.core import VoteITMF as _
from voteit.core.views.api import APIView
from voteit.core.security import ADD_PROPOSAL
from voteit.core.models.interfaces import IProposal
from voteit.core.security import RETRACT


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

    response = {}
    response['proposals'] = api.get_metadata_for_query(content_type = 'Proposal',
                                                       sort_index = 'created',
                                                       path = resource_path(context))
    response['api'] = api
    response['show_retract'] = _show_retract
    return render('../templates/proposals.pt', response, request = request)

@view_action('proposals', 'add_form', permission = ADD_PROPOSAL)
def proposals_dummy_form(context, request, va, **kw):
    api = kw['api']
    response = {}
    response['api'] = api
    response['url'] = api.resource_url(context, request)+"@@inline_form?content_type=Proposal"
    return render('../templates/snippets/inline_dummy_form.pt', response, request = request)
