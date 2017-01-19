from betahaus.viewcomponent.decorators import view_action
from pyramid.renderers import render

from voteit.core.models.interfaces import IMeeting
from voteit.core import _
from voteit.core.security import VIEW


@view_action('nav_right', 'polls',
             title = _("Polls"),
             priority = 3,
             containment = IMeeting,
             permission = VIEW,
             renderer = 'voteit.core:templates/snippets/polls_menu.pt')
def polls_menu(context, request, va, **kw):
    return render(va.kwargs['renderer'], {}, request = request)
