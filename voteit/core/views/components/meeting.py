from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.renderers import get_renderer

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IAgendaItem


@view_action('meeting_widgets', 'description_richtext', title = _(u"Description richtext field (default left column)"))
def description_richtext(context, request, va, **kw):
    return """<div class="description">%s</div>""" % context.description


@view_action('meeting_widgets', 'overview', title = _(u"Overview, displays poll times, winners and similar"))
def meeting_overview(context, request, va, **kw):

    def _check_section_closed(section):
        return request.cookies.get(section, None)

    response = {}
    response['api'] = kw['api']
    response['check_section_closed'] = _check_section_closed
    response['section_overview_macro'] = get_renderer('../templates/macros/meeting_overview_section.pt').implementation().macros['main']

    states = ('ongoing', 'upcoming', 'closed')
    over_limit = {}
    agenda_items = {}
    for state in states:
        if 'log_'+state in request.GET and request.GET['log_'+state] == 'all':
            limit = 0
        else:
            limit = 5
        ais = context.get_content(iface=IAgendaItem, states=state, sort_on='start_time')
        if limit and len(ais) > limit: #Over limit
            over_limit[state] = len(ais) - limit
            agenda_items[state] = ais[-limit:] #Only the 5 last entries
        else: #Not over limit
            over_limit[state] = 0
            agenda_items[state] = ais

    response['over_limit'] = over_limit
    response['agenda_items'] = agenda_items
    return render('../templates/snippets/meeting_overview.pt', response, request = request)

