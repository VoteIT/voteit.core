from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core import VoteITMF as _
from voteit.core.security import MODERATE_MEETING

@view_action('ai_widgets', 'proposals', title = _(u"Proposals (default left column)"))
def proposals(context, request, va, **kw):
    """ Render all proposal-related widgets. """
    api = kw['api']
        
    # build query string for show retraced link
    show_retracted_query = request.GET.copy()
    if not request.GET.get('show_retracted') == '1':
        show_retracted_query['show_retracted'] = 1
    elif 'show_retracted' in show_retracted_query:
        del show_retracted_query['show_retracted']
        
    show_retracted_url = api.request.resource_url(context, query=show_retracted_query)
        
    response = dict(
        proposal_widgets = api.render_view_group(context, request, 'proposals', **kw),
        api = api,
        context = context,
        show_retracted_url = show_retracted_url,
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

@view_action('agenda_item', 'edit_menu', permission=MODERATE_MEETING)
def edit_menu(context, request, va, **kw):
    response = {'api': kw['api']}
    return render('../templates/snippets/agenda_item_edit_menu.pt', response, request = request)
