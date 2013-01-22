from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from repoze.catalog.query import Any

from voteit.core import security
from voteit.core.models.interfaces import IPoll


@view_action('poll', 'listing', interface = IPoll)
def poll_listing(context, request, va, **kw):
    """ This is a view of a poll when it's displayed within an agenda item.
        It's not the listing for when a user votes.
    """
    api = kw['api']

    #The poll query doesn't have to care about path and such since we already have the uids
    query = Any('uid', context.proposal_uids)
    get_metadata = api.root.catalog.document_map.get_metadata

    count, docids = api.root.catalog.query(query, sort_index='created')
    results = []
    for docid in docids:
        results.append(get_metadata(docid))

    response = {}
    response['proposals'] = tuple(results)
    response['api'] = api
    response['poll_plugin'] = context.get_poll_plugin()
    response['can_vote'] = api.context_has_permission(security.ADD_VOTE, context)
    response['has_voted'] = api.userid in context
    response['wf_state'] = context.get_workflow_state()
    response['context'] = context #make sure context within the template is this context and nothing else
    return render('templates/polls/poll.pt', response, request = request)
