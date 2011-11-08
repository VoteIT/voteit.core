from betahaus.viewcomponent import view_action
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource
from betahaus.pyracont.factories import createSchema
from pyramid.renderers import render

from deform import Form
from voteit.core import VoteITMF as _
from voteit.core.security import ADD_DISCUSSION_POST
from voteit.core.security import DELETE
from voteit.core.models.schemas import button_add


@view_action('discussions', 'listing')
def discussions_listing(context, request, va, **kw):
    """ Get discussions for a specific context """
    api = kw['api']

    def _show_delete(brain):
        #Do more expensive checks last!
        if not api.userid in brain['creators']:
            return
        obj = find_resource(api.root, brain['path'])
        return api.context_has_permission(DELETE, obj)

    if request.GET.get('discussions', '') == 'all':
        limit = 0
    else:
        unread_count, content = api.search_catalog(context,
                                                   content_type = 'DiscussionPost',
                                                   unread = api.userid)
        limit = 5
        if unread_count > limit:
            limit = unread_count
    
    path = resource_path(context)
    query = dict(path = path,
                 content_type='DiscussionPost',
                 sort_index='created')
    #Returns tuple of (item count, iterator with docids)
    count, docids = api.search_catalog(**query)

    response = {}
    if limit:
        query['limit'] = limit
    response['discussions'] = api.get_metadata_for_query(**query)
    if limit and limit < count:
        response['over_limit'] = count - limit
    else:
        response['over_limit'] = 0
    response['limit'] = limit
    response['api'] = api
    response['show_delete'] = _show_delete
    return render('../templates/discussions.pt', response, request = request)

@view_action('discussions', 'add_form', permission = ADD_DISCUSSION_POST)
def discussions_dummy_form(context, request, va, **kw):
    api = kw['api']
    response = {}
    response['api'] = api
    response['url'] = api.resource_url(context, request)+"@@inline_form?content_type=DiscussionPost"
    return render('../templates/snippets/inline_dummy_form.pt', response, request = request)
