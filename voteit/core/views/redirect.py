from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config

from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IPoll


@view_config(context = IDiscussionPost, permission = NO_PERMISSION_REQUIRED)
@view_config(context = IPoll, permission = NO_PERMISSION_REQUIRED)
@view_config(context = IProposal, permission = NO_PERMISSION_REQUIRED)
def redirect_temp(request):
    """ Temporary fix until proper redirect with anchors is in place. """
    ai = request.agenda_item
    return HTTPFound(location = request.resource_url(ai, anchor = ai.uid))
