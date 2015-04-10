from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core.models.interfaces import IMeeting
from voteit.core import _
from voteit.core.security import VIEW
from voteit.core.models.interfaces import IAccessPolicy
from betahaus.viewcomponent.interfaces import IViewGroup
from betahaus.viewcomponent import render_view_group


@view_action('nav_right', 'meeting',
             title = _("Meeting"),
             priority = 1,
             containment = IMeeting,
             permission = VIEW,
             renderer = 'voteit.core:templates/snippets/meeting_menu.pt')
def meeting_menu(context, request, va, **kw):
    view = kw['view']
    ap = request.registry.queryAdapter(request.meeting, IAccessPolicy, name = request.meeting.access_policy)        
    response = {}
    response['ap_configurable'] = bool(ap is not None and ap.config_schema())
    response['view'] = view
    for name in ('meeting_menu', 'participants_menu', 'settings_menu'):
        if request.registry.queryUtility(IViewGroup, name):
            response[name] = render_view_group(context, request, name, spacer = " ")
        else:
            response[name] = ''
    return render(va.kwargs['renderer'], response, request = request)
