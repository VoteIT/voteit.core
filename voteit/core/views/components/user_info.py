from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path
from webhelpers.html.converters import nl2br

from voteit.core import VoteITMF as _
from pyramid.security import effective_principals
from voteit.core.models.interfaces import IUser
from voteit.core.helpers import strip_and_truncate


@view_action('user_info', 'basic_profile', interface = IUser)
def user_basic_profile(context, request, va, **kw):
    response = dict(
        about_me = nl2br(context.get_field_value('about_me')),
        api = kw['api'],
        context = context,
    )
    return render('../templates/snippets/user_basic_info.pt', response, request = request)

@view_action('user_info', 'latest_meeting_entries', interface = IUser)
def user_latest_meeting_entries(context, request, va, **kw):
    api = kw['api']
    query = {}
    #context is the user profile, but if within a meeting it's importat to preform a check
    #wether you're allowed to view entries
    #If the view that calls this is invoked outside a meeting, only admins and owners
    #will be able to view it.
    if api.meeting:
        query['path'] = resource_path(api.meeting)
        query['allowed_to_view'] = {'operator':'or', 'query': effective_principals(request)}
    else:
        query['path'] = resource_path(api.root)
    query['creators'] = context.userid
    query['content_type'] = {'query':('Proposal','DiscussionPost'), 'operator':'or'}
    query['sort_index'] = 'created'
    query['reverse'] = True
    query['limit'] = 5
    response = dict(
        last_entries = api.get_metadata_for_query(**query),
        api = api,
        context = context,
        truncate = strip_and_truncate,
    )
    return render('../templates/snippets/user_latest_meeting_entries.pt', response, request = request)

