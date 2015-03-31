from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core.security import MANAGE_SERVER
from voteit.core.security import MODERATE_MEETING
from voteit.core.security import VIEW
from voteit.core.security import MANAGE_GROUPS
from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IAccessPolicy


# @view_action('meeting_actions', 'admin_menu', title = _(u"Admin menu"), permission = MANAGE_SERVER,
#              menu_css_cls = 'admin_menu')
# @view_action('meeting_actions', 'settings_menu', title = _(u"Settings"), permission = MODERATE_MEETING,
#              meeting_only = True, menu_css_cls = 'settings_menu')
# @view_action('meeting_actions', 'meeting', title = _(u"Meeting"), permission=VIEW, meeting_only = True,
#              menu_css_cls = 'meeting_menu')
# @view_action('meeting_actions', 'participants_menu', title = _(u"Participants"), permission=VIEW,
#              meeting_only = True, menu_css_cls = 'participants_menu')
# @view_action('meeting_actions', 'help_action', title = _(u"Help & contact"),
#              menu_css_cls = 'help_contact_menu')
# def generic_menu(context, request, va, **kw):
#     api = kw['api']
#     if va.kwargs.get('meeting_only', False) == True and api.meeting is None:
#         return ''
#     response = {}
#     response['menu_title'] = va.title
#     response['menu_css_cls'] = va.kwargs.get('menu_css_cls', '')
#     response['rendered_menu'] = api.render_view_group(context, request, va.name)
#     return render('../templates/snippets/generic_meeting_menu.pt', response, request = request)


#FIXME:
#@view_action('admin_menu', 'moderators_emails', title = _(u"Moderators emails"), link = "moderators_emails")
#FIXME: @view_action('admin_menu', 'agenda_templates', title = _(u"Agenda templates"), link = "agenda_templates")
#@view_action('admin_menu', 'layout', title = _(u"Layout"), link = "layout") Use this?
def generic_root_menu_link(context, request, va, **kw):
    """ This is for simple menu items for the root """
    api = kw['api']
    url = api.resource_url(api.root, request) + va.kwargs['link']
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))

#@view_action('settings_menu', 'meeting_poll_settings', title = _(u"Meeting poll settings"),
#             link = "meeting_poll_settings", permission = MODERATE_MEETING)
# @view_action('settings_menu', 'agenda_templates', title = _(u"Agenda Templates"),
#              link = "agenda_templates", permission = MODERATE_MEETING)
#@view_action('settings_menu', 'access_policy', title = _(u"Access policy"),
#             link = "access_policy", permission = MODERATE_MEETING)
#@view_action('meeting', 'logs', title = _(u"Meeting actions log"), link = "logs", permission = MODERATE_MEETING)
#@view_action('meeting', 'minutes', title = _(u"Minutes"), link = "minutes")
# @view_action('settings_menu', 'participants_emails', title = _(u"Participants email addresses"),
#              link = "participants_emails", permission = MODERATE_MEETING)
# @view_action('participants_menu', 'manage_tickets', title = _(u"Manage invites"),
#              link = "manage_tickets", permission = MANAGE_GROUPS)
#@view_action('participants_menu', 'add_tickets', title = _(u"Invite participants"),
#             link = "add_tickets", permission = MANAGE_GROUPS)
#@view_action('participants_menu', 'add_participant', title = _(u"Add participant"),
#             link = "add_permission", permission = MANAGE_GROUPS)
#@view_action('participants_menu', 'participant_list', title = _(u"Participant list"), link = "participants")
#def generic_menu_link(context, request, va, **kw):
#    """ This is for simple menu items for the meeting root """
#    url = request.resource_url(request.meeting, va.kwargs['link'])

