from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import resource_path
from pyramid.view import view_config
from repoze.catalog.query import Eq

from voteit.core.security import MANAGE_SERVER
from voteit.core.security import MODERATE_MEETING
from voteit.core.security import VIEW
from voteit.core.security import MANAGE_GROUPS
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IMeeting


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
    query = Eq('content_type', 'Poll' ) & Eq('path', resource_path(api.meeting)) & Eq('workflow_state', 'ongoing')
    response = {}
    response['api'] = api
    response['menu_title'] = va.title
    response['open_polls'] = bool(api.root.catalog.query(query)[0])
    response['url'] = request.resource_url(api.meeting, 'meeting_poll_menu')
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

@view_action('admin_menu', 'moderators_emails', title = _(u"Moderators emails"), link = "moderators_emails")
@view_action('admin_menu', 'edit_root_permissions', title = _(u"Root permissions"), link = "permissions")
@view_action('admin_menu', 'server_log', title = _(u"Server logs"), link = "server_logs")
@view_action('admin_menu', 'agenda_templates', title = _(u"Agenda templates"), link = "agenda_templates")
@view_action('admin_menu', 'users', title = _(u"Users"), link = "users")
@view_action('admin_menu', 'layout', title = _(u"Layout"), link = "layout")
def generic_root_menu_link(context, request, va, **kw):
    """ This is for simple menu items for the root """
    api = kw['api']
    url = api.resource_url(api.root, request) + va.kwargs['link']
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))

@view_action('settings_menu', 'meeting_poll_settings', title = _(u"Meeting poll settings"),
             link = "meeting_poll_settings", permission = MODERATE_MEETING)
@view_action('settings_menu', 'agenda_templates', title = _(u"Agenda Templates"),
             link = "agenda_templates", permission = MODERATE_MEETING)
@view_action('settings_menu', 'access_policy', title = _(u"Access policy"),
             link = "access_policy", permission = MODERATE_MEETING)
@view_action('meeting', 'logs', title = _(u"Meeting actions log"), link = "logs", permission = MODERATE_MEETING)
@view_action('meeting', 'minutes', title = _(u"Minutes"), link = "minutes")
@view_action('settings_menu', 'participants_emails', title = _(u"Participants email addresses"),
             link = "participants_emails", permission = MODERATE_MEETING)
@view_action('participants_menu', 'manage_tickets', title = _(u"Manage invites"),
             link = "manage_tickets", permission = MANAGE_GROUPS)
@view_action('participants_menu', 'add_tickets', title = _(u"Invite participants"),
             link = "add_tickets", permission = MANAGE_GROUPS)
@view_action('participants_menu', 'add_participant', title = _(u"Add participant"),
             link = "add_permission", permission = MANAGE_GROUPS)
@view_action('participants_menu', 'participant_list', title = _(u"Participant list"), link = "participants")
def generic_menu_link(context, request, va, **kw):
    """ This is for simple menu items for the meeting root """
    url = request.resource_url(request.meeting, va.kwargs['link'])
    return """<li class="list-group-item"><a href="%s">%s</a></li>""" % (url, request.localizer.translate(va.title))

@view_action('settings_menu', 'configure_access_policy', title = _(u"Configure selected access policy"),
             link = "configure_access_policy", permission = MODERATE_MEETING)
def configure_access_policy_menu_link(context, request, va, **kw):
    """ Only show this if it has any settings to be configured """
    access_policy_name = request.meeting.get_field_value('access_policy', None)
    if not access_policy_name:
        return
    ap = request.registry.queryAdapter(request.meeting, IAccessPolicy, name = access_policy_name)
    if ap and ap.config_schema():
        url = request.resource_url(request.meeting, va.kwargs['link'])
        return """<li class="list-group-item"><a href="%s">%s</a></li>""" % (url, request.localizer.translate(va.title))


class MeetingActionsMenuBody(BaseView):
    
    @view_config(name="meeting_poll_menu", context=IMeeting, renderer="templates/polls/polls_menu_body.pt", permission=VIEW)
    def meeting_poll_menu(self):
        if self.api.show_moderator_actions:
            sections = MODERATOR_SECTIONS
        else:
            sections = REGULAR_SECTIONS
        meeting_path = resource_path(self.api.meeting)
        results = {}
        for section in sections:
            #Note, as long as we don't query for private wf state, we don't have to check perms
            num, docids = self.api.search_catalog(content_type = 'Poll',
                                                  path = meeting_path,
                                                  workflow_state = section)
            results[section] = [self.api.resolve_catalog_docid(x) for x in docids]
        self.response['sections'] = sections
        self.response['results'] = results
        return self.response
