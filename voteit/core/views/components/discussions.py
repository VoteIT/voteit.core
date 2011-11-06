from betahaus.viewcomponent import view_action
from pyramid.traversal import resource_path
from betahaus.pyracont.factories import createSchema
from pyramid.renderers import render

from deform import Form
from voteit.core import VoteITMF as _
from voteit.core.security import ADD_DISCUSSION_POST
from voteit.core.models.schemas import button_add


@view_action('discussions', 'listing')
def discussions_listing(context, request, va, **kw):
    """ Get discussions for a specific context """
    api = kw['api']
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
    #Returns tuple of (item_count, list of docids)
    count, docids = api.search_catalog(path=path, content_type='DiscussionPost', sort_index='created')
    docids = tuple(docids) #Convert, since it's a generator
    
    #Only fetch metadata that is within limit
    discussions = [api.resolve_catalog_docid(x) for x in docids[-limit:]]

    response = {}
    response['discussions'] = tuple(discussions)
    if limit and limit < count:
        response['over_limit'] = count - limit
    else:
        response['over_limit'] = 0
    response['limit'] = limit
    response['like'] = _(u"Like")
    response['like_this'] = _(u"like this")
    response['api'] = api
    return render('../templates/discussions.pt', response, request = request)


@view_action('discussions', 'add_form', permission = ADD_DISCUSSION_POST)
def discussions_add_form(context, request, va, **kw):
    api = kw['api']
    url = api.resource_url(context, request)
    schema = createSchema('DiscussionPostSchema').bind(context = context, request = request)
    form = Form(schema, action=url+"@@add?content_type=DiscussionPost", buttons=(button_add,))
    api.register_form_resources(form)
    response = {}
    response['form'] = form.render()
    response['api'] = api
    return render('../templates/snippets/inline_add_form.pt', response, request = request)
