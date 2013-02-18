from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.exceptions import NotFound

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IProposal


@view_config(context=IDiscussionPost)
def discussion_redirect_to_agenda_item(context, request):
    root = find_root(context)
    ai = find_interface(context, IAgendaItem)
    if ai:
        path = resource_path(ai)
        
        query = dict(path = path,
                     content_type='DiscussionPost',
                     sort_index='created',
                     reverse=True,
                     limit=5, #FIXME: this should be globaly configurable?
                     )
        docids = root.catalog.search(**query)[1]
        
        # set to True if requested post is after the display limit
        after_limit = False
        
        get_metadata = root.catalog.document_map.get_metadata
        for docid in docids:
            brain = get_metadata(docid)
            if brain['uid'] == context.uid:
                after_limit = True
                break
            
        # post was not found among the displayed posts
        query = request.GET
        if not after_limit:
            query['discussions'] = 'all'
            url = request.resource_url(ai, query=query, anchor=context.uid)
        else:
            url = request.resource_url(ai, query=query, anchor=context.uid)
        return HTTPFound(location=url)
    
    raise NotFound("Couldn't locate Agenda Item from this context.")

@view_config(context=IProposal)
def proposal_redirect_to_agenda_item(context, request):
    ai = find_interface(context, IAgendaItem)
    if ai:
        query = request.GET
        url = request.resource_url(ai, query=query, anchor=context.uid)
        return HTTPFound(location=url)
    raise NotFound("Couldn't locate Agenda Item from this context.")

