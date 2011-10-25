from betahaus.viewcomponent import view_action
from betahaus.pyracont.factories import createSchema
from pyramid.renderers import render

from deform import Form
from voteit.core import VoteITMF as _
from voteit.core.security import ADD_PROPOSAL
from voteit.core.models.schemas import button_add
from voteit.core.models.interfaces import IProposal


@view_action('proposals', 'listing')
def proposal_listing(context, request, va, **kw):
    """ Get proposals for a specific context """
    #FIXME: This view should use catalog metadata instead.
    #We can fetch the object if show-restract passes wf condition
    api = kw['api']

    def _show_retract(obj):
        return api.context_has_permission('Retract', obj) and \
            obj.get_workflow_state() == 'published'

    response = {}
    response['proposals'] = context.get_content(iface=IProposal, sort_on='created')
    response['like'] = _(u"Like")
    response['like_this'] = _(u"like this")
    response['api'] = api
    response['show_retract'] = _show_retract
    return render('../templates/proposals.pt', response, request = request)


@view_action('proposals', 'add_form', permission = ADD_PROPOSAL)
def discussions_add_form(context, request, va, **kw):
    api = kw['api']
    url = api.resource_url(context, request)
    schema = createSchema('ProposalSchema').bind(context = context, request = request)
    form = Form(schema, action=url+"@@add?content_type=Proposal", buttons=(button_add,))
    api.register_form_resources(form)
    response = {}
    response['form'] = form.render()
    response['api'] = api
    return render('../templates/snippets/proposal_form.pt', response, request = request)
