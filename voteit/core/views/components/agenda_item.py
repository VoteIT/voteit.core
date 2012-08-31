from betahaus.viewcomponent import view_action
from voteit.core import VoteITMF as _
from pyramid.renderers import render


@view_action('ai_widgets', 'proposals', title = _(u"Proposals (default left column)"))
def proposals(context, request, va, **kw):
    """ Render all proposal-related widgets. """
    api = kw['api']
    response = dict(
        proposal_widgets = api.render_view_group(context, request, 'proposals', **kw),
        api = api,
        context = context,
    )
    return render('../templates/snippets/ai_proposals.pt', response, request = request)

@view_action('ai_widgets', 'discussions', title = _(u"Discussions (default right column)"))
def discussions(context, request, va, **kw):
    """ Render all discussion-related widgets. """
    api = kw['api']
    response = dict(
        discussion_widgets = api.render_view_group(context, request, 'discussions', **kw),
        api = api,
        context = context,
    )
    return render('../templates/snippets/ai_discussions.pt', response, request = request)
