from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path

from voteit.core import VoteITMF as _
from voteit.core.security import MODERATE_MEETING
from voteit.core.security import ADD_MEETING
from voteit.core.security import VIEW
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot


@view_action('sidebar', 'navigation')
def navigation(context, request, va, **kwargs):
    api = kwargs['api']
    if api.meeting:
        nav_out = api.render_view_group(api.meeting, request, 'navigation_sections', **kwargs)
    else:
        nav_out = api.render_view_group(api.root, request, 'navigation_sections', **kwargs)
    if nav_out:
        return '<div id="navigation" class="sidebar_block">%s</div>' % nav_out
    return u""

@view_action('navigation_sections', 'navigation_section_header', permission = VIEW)
def navigation_section_header(context, request, va, **kwargs):
    api = kwargs['api']
    if not api.userid:
        return u""
    if api.meeting:
        title = _(u"Agenda")
        description = _(u"Click to go to meeting overview")
        url = api.meeting_url
    else:
        title = _(u"Meetings")
        description = u""
        url = request.resource_url(api.root),
    response = dict(
        api = api,
        title = title,
        description = description,
        url = url,
        show_add_meeting = not api.meeting and api.context_has_permission(ADD_MEETING, api.root),
    )
    return render('templates/sidebars/navigation_head.pt', response, request = request)

@view_action('navigation_sections', 'ongoing', title = _(u"Ongoing"), state = 'ongoing', permission = VIEW)
@view_action('navigation_sections', 'upcoming', title = _(u"Upcoming"), state = 'upcoming', permission = VIEW)
@view_action('navigation_sections', 'closed', title = _(u"Closed"), state = 'closed', permission = VIEW)
@view_action('navigation_sections', 'private', title = _(u"Private"), state = 'private',
             permission = MODERATE_MEETING, interface = IMeeting)
def navigation_sections(context, request, va, **kwargs):
    """ Navigation sections. These doesn't work for unauthenticated currently. """
    api = kwargs['api']
    if not api.userid:
        return u""
    state = va.kwargs['state']
    response = {}
    response['api'] = api
    response['state'] = state
    response['section_title'] = va.title
    response['toggle_id'] = '%s-%s' % (context.uid, state)

    if request.cookies.get(response['toggle_id']):
        response['closed_section'] = True
        return render('templates/sidebars/navigation_section.pt', response, request = request)

    context_path = resource_path(context)
    query = dict(
        workflow_state = state,
        path = context_path,
    )
    #Meeting or root context?
    if ISiteRoot.providedBy(context):
        query['content_type'] = 'Meeting'
        #Note that None is not a valid query. This view shouldn't be called for unauthenticated.
        query['view_meeting_userids'] = api.userid
    else:
        query['content_type'] = 'AgendaItem'
        #Principals taken from this context will be okay for a query within the meetings
        query['allowed_to_view'] = {'operator': 'or', 'query': api.context_effective_principals(context)}
        query['sort_index'] = 'order'
    
    def _count_query(path, content_type, unread = False):
        """ Returns number of an item, possbly unread only. """
        query = {}
        query['path'] = path
        query['content_type'] = content_type
        
        if content_type == 'Proposal':
            query['workflow_state'] = {'query':('published', 'retracted', 'unhandled', 'voting', 'approved', 'denied'), 'operator':'or'}        
        if unread:
            query['unread'] = api.userid
        return api.search_catalog(**query)[0]
    
    def _in_current_context(path, context_path):
        path = path.split('/')
        context_path = context_path.split('/')
        if len(path) > len(context_path):
            path = path[0:len(context_path)]
            
        return path == context_path

    response['brains'] = api.get_metadata_for_query(**query)
    response['context_path'] = context_path
    response['count_query'] = _count_query
    response['closed_section'] = False
    response['in_current_context'] = _in_current_context
    return render('templates/sidebars/navigation_section.pt', response, request = request)
