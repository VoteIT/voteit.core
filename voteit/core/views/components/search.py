from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core import VoteITMF as _
from voteit.core.security import VIEW
from voteit.core.models.interfaces import IMeeting


@view_action('main', 'search', permission=VIEW)
def meeting_actions(context, request, va, **kw):
    api = kw['api']
    response = {'api': api}
    return render('templates/header/search.pt', response, request = request)
