from betahaus.viewcomponent.decorators import view_action

from voteit.core.models.interfaces import IMeeting
from voteit.core import _
from pyramid.renderers import render


@view_action('nav_right', 'polls',
             title = _("Workflow"),
             priority = 5,
             containment = IMeeting,
             renderer = 'voteit.core:templates/snippets/polls_menu.pt')
def polls_menu(context, request, va, **kw):
    return render(va.kwargs['renderer'], {}, request = request)
