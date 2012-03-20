from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from deform import Form
from pyramid.url import resource_url
from betahaus.pyracont.factories import createSchema
from voteit.core.models.schemas import button_login
from voteit.core.security import ADD_MEETING
from voteit.core.security import MODERATE_MEETING
from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IMeeting, ISiteRoot
from pyramid.traversal import resource_path


@view_action('main', 'navigation')
def navigation(context, request, va, **kwargs):
    response = dict(
        api = kwargs['api']
    )
    return render('../templates/navigation.pt', response, request = request)

@view_action('navigation', 'login')
def login_box(context, request, va, **kwargs):
    api = kwargs['api']

    #FIXME: Ticket system makes it a bit of a hassle to make login detached from registration.
    #We'll do that later. For now, let's just check if user is on login or registration page

    url = request.path_url
    if url.endswith('login') or url.endswith('register'):
        return u""
    login_schema = createSchema('LoginSchema').bind(context = context, request = request)
    action_url = resource_url(api.root, request) + 'login'
    login_form = Form(login_schema, buttons=(button_login,), action=action_url)
    api.register_form_resources(login_form)
    return """%s<div><a href="/@@request_password">%s</a></div>""" % (login_form.render(), api.translate(_(u"Forgot password?")))
    
@view_action('navigation_sections', 'ongoing', title = _(u"Ongoing"), state = 'ongoing')
@view_action('navigation_sections', 'upcoming', title = _(u"Upcoming"), state = 'upcoming')
@view_action('navigation_sections', 'closed', title = _(u"Closed"), state = 'closed')
@view_action('navigation_sections', 'private', title = _(u"Private"), state = 'private',
             permission = MODERATE_MEETING, interface = IMeeting)
def navigation_section(context, request, va, **kwargs):
    api = kwargs['api']
    state = va.kwargs['state']

    response = {}
    response['api'] = api
    response['state'] = state
    response['section_title'] = va.title
    response['toggle_id'] = '%s-%s' % (context.uid, state)

    if request.cookies.get(response['toggle_id']):
        response['closed_section'] = True
        return render('../templates/snippets/navigation_section.pt', response, request = request)

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
        if unread:
            return api.search_catalog(path = path, content_type = content_type, unread = api.userid)[0]
        return api.search_catalog(path = path, content_type = content_type)[0]
    
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
    return render('../templates/snippets/navigation_section.pt', response, request = request)
