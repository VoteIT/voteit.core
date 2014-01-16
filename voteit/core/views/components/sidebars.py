from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from zope.interface.interfaces import ComponentLookupError

from voteit.core import VoteITMF as _


@view_action('sidebar', 'login_alt')
def alternative_login_methods(context, request, va, **kwargs):
    api = kwargs['api']
    if api.userid:
        return u""
    try:
        alt_out = api.render_view_group(api.root, request, 'login_forms', **kwargs)
        if alt_out:
            return render('templates/sidebars/login_alt.pt', {'api': api, 'alt_out': alt_out}, request = request)
    except ComponentLookupError: #There's no login_forms view group
        pass
    return u""

@view_action('sidebar', 'latest_meeting_entries')
def latest_meeting_entries(context, request, va, **kwargs):
    #FIXME: This is disabled for now, needs proper design
    return ''
#    api = kwargs['api']
#    
#    # only avaible in meeting
#    if not api.meeting:
#        return ''
#    
#    response = dict(
#        api = api,
#        context = context,
#        truncate = strip_and_truncate,
#        closed_section = False,
#    )
#    
#    if request.cookies.get('latest_meeting_entries'):
#        response['closed_section'] = True
#        return render('../templates/snippets/latest_meeting_entries.pt', response, request = request)
#    
#    response['closed_section'] = False
#    
#    query = {}
#    query['path'] = resource_path(api.meeting)
#    query['allowed_to_view'] = {'operator':'or', 'query': effective_principals(request)}
#    query['content_type'] = {'query':('Proposal','DiscussionPost'), 'operator':'or'}
#    query['sort_index'] = 'created'
#    query['reverse'] = True
#    query['limit'] = 5
#    
#    response['last_entries'] = api.get_metadata_for_query(**query)
#    
#    return render('../templates/snippets/latest_meeting_entries.pt', response, request = request)
