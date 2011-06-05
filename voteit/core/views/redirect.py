from pyramid.traversal import find_interface
from pyramid.view import view_config
from pyramid.url import resource_url
from webob.exc import HTTPFound
from pyramid.exceptions import NotFound

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IProposal


@view_config(context=IDiscussionPost)
@view_config(context=IProposal)
def redirect_to_agenda_item(context, request):
    ai = find_interface(context, IAgendaItem)
    if ai:
        url = resource_url(ai, request)
        return HTTPFound(location=url)
    raise NotFound("Couldn't locate Agenda Item from this context.")

