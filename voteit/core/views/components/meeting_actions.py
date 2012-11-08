from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path
from pyramid.view import view_config
from repoze.catalog.query import Eq
from repoze.catalog.query import NotAny

from voteit.core.security import MANAGE_SERVER, MODERATE_MEETING
from voteit.core.security import VIEW
from voteit.core.security import EDIT
from voteit.core.security import MANAGE_GROUPS
from voteit.core.security import ADD_VOTE
from voteit.core import VoteITMF as _
from voteit.core.views.api import APIView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.catalog import resolve_catalog_docid


MODERATOR_SECTIONS = ('closed', 'ongoing', 'upcoming', 'private',)
REGULAR_SECTIONS = ('closed', 'ongoing', 'upcoming',)


@view_action('main', 'meeting_actions', permission=VIEW)
def meeting_actions(context, request, va, **kw):
    """ This is the main renderer for meeting actions.
        The structure of the menu. it will call all view components
        in the group meeting_actions.
        In turn, some of those will call other groups.
    """
    api = kw['api']
    context = api.meeting and api.meeting or api.root
    return """<ul id="meeting-actions-menu">%s</ul>""" % api.render_view_group(context, request, 'meeting_actions')


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
    return render('../templates/snippets/polls_menu.pt', response, request = request)

@view_action('meeting_actions', 'help_contact', title = _(u"Help & contact"), permission=VIEW)
def help_contact_menu(context, request, va, **kw):
    api = kw['api']
    return """<li id="help-tab" class="tab"><a href="#">%s</a></li>""" % api.translate(va.title)

@view_action('meeting_actions', 'search', title = _(u"Search"), permission=VIEW)
def search_menu(context, request, va, **kw):
    api = kw['api']
    if api.meeting:
        return u"""<li class="tab"><a href="%ssearch">%s</a></li>""" % (api.meeting_url, api.translate(va.title))
    return u""


@view_action('meeting_actions', 'admin_menu', title = _(u"Admin menu"), permission = MANAGE_SERVER)
@view_action('meeting_actions', 'settings_menu', title = _(u"Settings"), permission = MODERATE_MEETING, meeting_only = True)
@view_action('meeting_actions', 'meeting', title = _(u"Meeting"), permission=VIEW, meeting_only = True)
@view_action('meeting_actions', 'participants_menu', title = _(u"Participants"), permission=VIEW, meeting_only = True, menu_css_cls = 'user-dark')
def generic_menu(context, request, va, **kw):
    api = kw['api']
    if va.kwargs.get('meeting_only', False) == True and api.meeting is None:
        return ''
    response = {}
    response['menu_title'] = va.title
    response['menu_css_cls'] = va.kwargs.get('menu_css_cls', False) or 'cog-dark'
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
#FIXME: Remove below alternative, it's linked to participants now
@view_action('participants_menu', 'permissions', title = _(u"Edit permissions"), link = "participants", permission = MANAGE_GROUPS)
@view_action('participants_menu', 'manage_tickets', title = _(u"Manage invites"), link = "manage_tickets", permission = MANAGE_GROUPS)
@view_action('participants_menu', 'add_tickets', title = _(u"Invite participants"), link = "add_tickets", permission = MANAGE_GROUPS)
@view_action('participants_menu', 'add_participant', title = _(u"Add participant"), link = "add_permission", permission = MANAGE_GROUPS)
@view_action('participants_menu', 'participant_list', title = _(u"Participant list"), link = "participants")
def generic_menu_link(context, request, va, **kw):
    """ This is for simple menu items for the meeting root """
    api = kw['api']
    url = "%s%s" % (api.meeting_url, va.kwargs['link'])
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))


@view_config(name="meeting_poll_menu", context=IMeeting, renderer="../templates/snippets/polls_menu_body.pt", permission=VIEW)
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

    response = {}
    response['api'] = api
    response['sections'] = sections
    response['show_polls'] = show_polls
    response['polls_metadata'] = metadata
    return response

