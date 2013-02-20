from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource
from pyramid.view import view_config
from repoze.catalog.query import Eq
from repoze.catalog.query import NotAny

from voteit.core.security import MANAGE_SERVER
from voteit.core.security import MODERATE_MEETING
from voteit.core.security import VIEW
from voteit.core.security import MANAGE_GROUPS
from voteit.core.security import ADD_VOTE
from voteit.core import VoteITMF as _
from voteit.core.views.api import APIView
from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.catalog import resolve_catalog_docid


MODERATOR_SECTIONS = ('ongoing', 'upcoming', 'closed', 'private',)
REGULAR_SECTIONS = ('ongoing', 'upcoming', 'closed',)


@view_action('main', 'meeting_actions', permission=VIEW)
def meeting_actions(context, request, va, **kw):
    """ This is the main renderer for meeting actions.
        The structure of the menu. it will call all view components
        in the group meeting_actions.
        In turn, some of those will call other groups.
    """
    api = kw['api']
    context = api.meeting and api.meeting or api.root
    return """<ul id="meeting-actions-menu" class="actions-menu">%s</ul>""" % api.render_view_group(context, request, 'meeting_actions')


@view_action('meeting_actions', 'polls', title = _(u"Polls"), permission=VIEW)
def polls_menu(context, request, va, **kw):
    api = kw['api']
    if api.meeting is None:
        return ''

    response = {}
    response['api'] = api
    response['menu_title'] = va.title
    
    # get all polls that is ongoing an the user hasn't voted in yet
    query = Eq('content_type', 'Poll' ) & \
            Eq('path', resource_path(api.meeting)) & \
            Eq('workflow_state', 'ongoing') & \
            NotAny('voted_userids', api.userid)
    num, results = api.root.catalog.query(query)
    
    # count the polls the user has the right to vote in
    num = 0
    for docid in results:
        poll = resolve_catalog_docid(api.root.catalog, api.root, docid)
        if api.context_has_permission(ADD_VOTE, poll):
            num = num + 1

    response['unvoted_polls_count'] = num
    response['url'] = '%smeeting_poll_menu' % api.resource_url(api.meeting, request)
    return render('templates/polls/polls_menu.pt', response, request = request)


@view_action('meeting_actions', 'admin_menu', title = _(u"Admin menu"), permission = MANAGE_SERVER,
             menu_css_cls = 'admin_menu')
@view_action('meeting_actions', 'settings_menu', title = _(u"Settings"), permission = MODERATE_MEETING,
             meeting_only = True, menu_css_cls = 'settings_menu')
@view_action('meeting_actions', 'meeting', title = _(u"Meeting"), permission=VIEW, meeting_only = True,
             menu_css_cls = 'meeting_menu')
@view_action('meeting_actions', 'participants_menu', title = _(u"Participants"), permission=VIEW,
             meeting_only = True, menu_css_cls = 'participants_menu')
@view_action('meeting_actions', 'help_action', title = _(u"Help & contact"),
             menu_css_cls = 'help_contact_menu')
def generic_menu(context, request, va, **kw):
    api = kw['api']
    if va.kwargs.get('meeting_only', False) == True and api.meeting is None:
        return ''
    response = {}
    response['menu_title'] = va.title
    response['menu_css_cls'] = va.kwargs.get('menu_css_cls', '')
    response['rendered_menu'] = api.render_view_group(context, request, va.name)
    return render('../templates/snippets/generic_meeting_menu.pt', response, request = request)


@view_action('admin_menu', 'recaptcha', title = _(u"ReCaptcha"), link = "recaptcha")
@view_action('admin_menu', 'edit_root_permissions', title = _(u"Root permissions"), link = "permissions")
@view_action('admin_menu', 'server_log', title = _(u"Server logs"), link = "server_logs")
@view_action('admin_menu', 'agenda_templates', title = _(u"Agenda templates"), link = "agenda_templates")
@view_action('admin_menu', 'users', title = _(u"Users"), link = "users")
def generic_root_menu_link(context, request, va, **kw):
    """ This is for simple menu items for the root """
    api = kw['api']
    url = api.resource_url(api.root, request) + va.kwargs['link']
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))


@view_action('settings_menu', 'meeting_poll_settings', title = _(u"Meeting poll settings"), link = "meeting_poll_settings", permission = MODERATE_MEETING)
@view_action('settings_menu', 'agenda_templates', title = _(u"Agenda Templates"), link = "agenda_templates", permission = MODERATE_MEETING)
@view_action('settings_menu', 'manage_layout', title = _(u"Layout and widgets"), link = "manage_layout", permission = MODERATE_MEETING)
@view_action('settings_menu', 'access_policy', title = _(u"Access policy"), link = "access_policy", permission = MODERATE_MEETING)
@view_action('settings_menu', 'mail_settings', title = _(u"Mail settings"), link = "mail_settings", permission = MODERATE_MEETING)
@view_action('settings_menu', 'presentation', title = _(u"Presentation"), link = "presentation", permission = MODERATE_MEETING)
@view_action('meeting', 'logs', title = _(u"Meeting actions log"), link = "logs", permission = MODERATE_MEETING)
@view_action('meeting', 'minutes', title = _(u"Minutes"), link = "minutes")
@view_action('participants_menu', 'participants_emails', title = _(u"Participants email addresses"), link = "participants_emails", permission = MODERATE_MEETING)
@view_action('participants_menu', 'manage_tickets', title = _(u"Manage invites"), link = "manage_tickets", permission = MANAGE_GROUPS)
@view_action('participants_menu', 'add_tickets', title = _(u"Invite participants"), link = "add_tickets", permission = MANAGE_GROUPS)
@view_action('participants_menu', 'add_participant', title = _(u"Add participant"), link = "add_permission", permission = MANAGE_GROUPS)
@view_action('participants_menu', 'participant_list', title = _(u"Participant list"), link = "participants")
def generic_menu_link(context, request, va, **kw):
    """ This is for simple menu items for the meeting root """
    api = kw['api']
    url = "%s%s" % (api.meeting_url, va.kwargs['link'])
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))

@view_action('settings_menu', 'configure_access_policy', title = _(u"Configure selected access policy"),
             link = "configure_access_policy", permission = MODERATE_MEETING)
def configure_access_policy_menu_link(context, request, va, **kw):
    """ Only show this if it has any settings to be configured """
    api = kw['api']
    if not api.meeting:
        return u""
    access_policy_name = api.meeting.get_field_value('access_policy', None)
    if not access_policy_name:
        return u""
    ap = request.registry.queryAdapter(api.meeting, IAccessPolicy, name = access_policy_name)
    if ap and ap.configurable:
        url = "%s%s" % (api.meeting_url, va.kwargs['link'])
        return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))
    return u""

@view_config(name="meeting_poll_menu", context=IMeeting, renderer="templates/polls/polls_menu_body.pt", permission=VIEW)
def meeting_poll_menu(context, request):
    api = APIView(context, request)
    if api.meeting is None:
        return ''
    if api.show_moderator_actions:
        sections = MODERATOR_SECTIONS
    else:
        sections = REGULAR_SECTIONS

    metadata = {}
    meeting_path = resource_path(api.meeting)
    show_polls = False
    for section in sections:
        #Note, as long as we don't query for private wf state, we don't have to check perms
        metadata[section] = api.get_metadata_for_query(content_type = 'Poll',
                                                        path = meeting_path,
                                                        workflow_state = section)
        if metadata[section]:
            show_polls = True

    def _get_poll_url(path):
        poll = find_resource(api.root, path)
        return request.resource_url(poll.__parent__, anchor=poll.uid)

    response = {}
    response['get_poll_url'] = _get_poll_url
    response['api'] = api
    response['sections'] = sections
    response['show_polls'] = show_polls
    response['polls_metadata'] = metadata
    return response

