from betahaus.viewcomponent import view_action
from betahaus.viewcomponent.interfaces import IViewGroup
from pyramid.renderers import render

from voteit.core import VoteITMF as _
from voteit.core.security import MODERATE_MEETING


@view_action('tabs', 'manage_agenda', permission = MODERATE_MEETING)
def render_tabs_menu(context, request, va, **kw):
    """ Render tabs from a specific view group. This is to make the tabs pluggable. """
    view_group = request.registry.queryUtility(IViewGroup, name = va.name)
    if not view_group:
        return u""
    tabs = [x(context, request, **kw) for x in view_group.values()]
    if not tabs:
        return u""
    response = {'api': kw['api'], 'tabs': tabs}
    return render('templates/tabs_menu.pt', response, request = request)
