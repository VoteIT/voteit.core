from betahaus.viewcomponent import view_action
from betahaus.pyracont.factories import createSchema
from pyramid.renderers import render
from pyramid.traversal import resource_path, find_resource

from deform import Form
from voteit.core import VoteITMF as _
from voteit.core.security import ADD_PROPOSAL
from voteit.core.models.schemas import button_add
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
        if not api.userid in brain['creators'] and not api.show_moderator_actions:
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
def proposals_add_form(context, request, va, **kw):
    api = kw['api']
    url = api.resource_url(context, request)
    schema = createSchema('ProposalSchema').bind(context = context, request = request)
    form = Form(schema, action=url+"@@add?content_type=Proposal", buttons=(button_add,))
    api.register_form_resources(form)
    response = {}
    response['form'] = form.render()
    response['api'] = api
    return render('../templates/snippets/inline_add_form.pt', response, request = request)
