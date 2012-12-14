from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core import VoteITMF as _
from voteit.core.security import VIEW
from voteit.core.models.interfaces import IMeeting


@view_action('main', 'search', permission=VIEW, containment = IMeeting)
def meeting_actions(context, request, va, **kw):
    api = kw['api']
    response = {'api': api}
    #FIXME: discriminators don't work on render single view component. Untill that has
    #been fixed or it's actually possible to search in root, keep this code:
    if not api.meeting:
        return u""
    return render('templates/header/search.pt', response, request = request)
