from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from repoze.catalog.query import NotAny
from zope.component.interfaces import ComponentLookupError

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IAgendaItem


@view_action('proposals', 'listing', interface = IAgendaItem)
def proposal_listing(context, request, va, **kw):
    """ Get proposals for a specific context.
    """
    api = kw['api']

    #Start with checking which polls that exist in this context and store shown uids
    shown_uids = set()
    polls = []
    for poll in api.get_restricted_content(context, iface=IPoll, sort_on='created'):
        try:
            plugin = poll.get_poll_plugin()
        except ComponentLookupError:
            err_msg = _(u"plugin_missing_error",
                        default = u"Can't find any poll plugin with name '${name}'. Perhaps that package has been uninstalled?",
                        mapping = {'name': poll.get_field_value('poll_plugin')})
            api.flash_messages.add(err_msg, type="error")
            continue
        shown_uids.update(poll.proposal_uids)
        polls.append(poll)

    #The agenda item query must be based on the context and to exclude all already shown
    #This view also cares about retracted proposals where as poll version doesn't
    #if api.meeting.get_field_value('show_retracted', True) or request.GET.get('show_retracted') == '1':
    #    wf_states = ('published', 'retracted', 'locked', 'unhandled') #More?
    #else:
    #    wf_states = ('published', 'retracted', 'locked')
    #FIXME: Show retracted stuff
    #wf_states = ('published', 'retracted', 'locked', 'unhandled')
    
    query = Eq('path', resource_path(context)) &\
            Eq('content_type', 'Proposal') &\
            NotAny('uid', shown_uids)
            #(NotAny('uid', shown_uids) | Any('workflow_state', wf_states))

    tag = request.GET.get('tag', None)
    if tag:
        #Only apply tag limit for things that aren't polls.
        #This is a safegard against user errors
        query = query & Any('tags', (tag, ))
        
    # build query string and remove tag
    clear_tag_query = request.GET.copy()
    if 'tag' in clear_tag_query:
        del clear_tag_query['tag']

    count, docids = api.root.catalog.query(query, sort_index='created')
    get_metadata = api.root.catalog.document_map.get_metadata
    results = []
    for docid in docids:
        metadata = get_metadata(docid)
        results.append(metadata)

    response = {}
    response['clear_tag_url'] = request.resource_url(context, query=clear_tag_query)
    response['proposals'] = tuple(results)
    response['tag'] = tag
    response['api'] = api 
    response['polls'] = polls
    return render('templates/proposals/listing.pt', response, request = request)


@view_action('proposal', 'block')
def proposal_block(context, request, va, **kw):
    """ This is the view group for each individual proposal. """
    api = kw['api']
    brain = kw['brain']
    response = {}
    response['api'] = api
    response['brain'] = brain
    return render('../templates/proposal.pt', response, request=request)
