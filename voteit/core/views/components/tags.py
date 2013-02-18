from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.security import effective_principals
from pyramid.traversal import resource_path
from repoze.catalog.query import Eq
from repoze.catalog.query import Any

from voteit.core import VoteITMF as _


@view_action('agenda_item_top', 'tag_stats')
def tag_stats(context, request, *args, **kwargs):
    api = kwargs['api']
    if not api.meeting:
        return ""

    query = Eq('path', resource_path(context)) &\
            Any('allowed_to_view', effective_principals(request)) &\
            Any('content_type', ('Proposal', 'DiscussionPost',))

    num, docids = api.root.catalog.query(query)
    unique_tags = set()
    #FIXME: There must be a smarter way to load uniques!?
    for docid in docids:
        entry = api.root.catalog.document_map.get_metadata(docid)
        unique_tags.update(entry['tags'])

    results = []
    for tag in unique_tags:
        count = api.get_tag_count(tag)
        if count > 1:
            results.append((tag, count))

    if not results:
        return u""

    #Sort the tags based on occurence and show the top 5
    results = sorted(results, key=lambda x: x[1], reverse = True)[:5]

    def _make_url(tag):
        query = request.GET.copy()
        query['tag'] = tag
        return request.resource_url(context, query=query)

    response = dict(
        api = api,
        context = context,
        stats = results,
        make_url = _make_url,
    )
    return render('templates/tag_stats.pt', response, request = request)
