from arche.views.base import DefaultEditForm
from betahaus.viewcomponent import render_view_group
from betahaus.viewcomponent import view_action
from pyramid.view import view_config
from pyramid.renderers import render
from zope.interface.interfaces import ComponentLookupError

from voteit.core import security
from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IMeeting
from voteit.core.views.base_edit import ArcheFormCompat
from voteit.core import _


TPL = 'voteit.core:templates/menus/control_panel_item.pt'


def agenda_labels_active(context, request, va):
    return bool(context.tags)


@view_action('control_panel', 'proposal',
             panel_group = 'control_panel_proposal',
             title=_("Proposals"),
             description=_(
                 "control_panel_proposal_description",
                 default="Change behaviour of proposals and set "
                         "users that moderators may add proposals as."))
@view_action('control_panel', 'poll',
             panel_group = 'control_panel_poll',
             title=_("Polls and votes"))
@view_action('control_panel', 'notifications',
             panel_group = 'control_panel_notifications',
             title=_("Notifications"))
@view_action('control_panel', 'agenda_labels',
             panel_group = 'control_panel_agenda_labels',
             title=_("Agenda labels"),
             check_active=agenda_labels_active)
def control_panel_category(context, request, va, active=True, **kw):
    """
    check_active
    """
    check_active = va.kwargs.get('check_active', False)
    if check_active:
        is_active = bool(check_active(context, request, va))
    else:
        is_active = True
    if active == is_active:
        response = {
            'context': context,
            'title': va.title,
            'description': va.kwargs.get('description', ''),
        }
        try:
            response['panel_group'] = render_view_group(context, request, va.kwargs['panel_group'])
        except ComponentLookupError:
            response['panel_group'] = ''
        renderer = va.kwargs.get('renderer', None)
        tpl = renderer and renderer or TPL
        return render(tpl, response, request=request)


@view_action('control_panel', 'access_policy',
             panel_group='control_panel_access_policy',
             title=_("Access policy"))
def control_panel_ap(context, request, va, active=True, **kw):
    """ Access policy control panel. """
    if active:
        ap_name = request.meeting.access_policy
        if not ap_name:
            ap_name = 'invite_only'
        ap = request.registry.queryAdapter(request.meeting, IAccessPolicy, name=ap_name)
        response = {
            'context': context,
            'title': va.title,
            'access_policy': ap,
            'ap_configurable': bool(ap is not None and ap.config_schema()),
        }
        try:
            response['panel_group'] = render_view_group(context, request, va.kwargs['panel_group'])
        except ComponentLookupError:
            response['panel_group'] = ''
        return render('voteit.core:templates/menus/control_panel_ap.pt', response, request=request)


@view_action('control_panel', 'participants',
             panel_group='control_panel_participants',
             title=_("Participants"))
def control_panel_participants(context, request, va, active=True, **kw):
    """ Participants control panel. """
    if active:
        response = {
            'context': context,
            'title': va.title,
            'meeting_closed': context.get_workflow_state() == 'closed',
        }
        try:
            response['panel_group'] = render_view_group(context, request, va.kwargs['panel_group'])
        except ComponentLookupError:
            response['panel_group'] = ''
        return render('voteit.core:templates/menus/control_panel_participants.pt', response, request=request)


@view_action('control_panel_proposal', 'settings',
             title=_("Settings"), view_name='proposal_settings')
@view_action('control_panel_poll', 'settings',
             title=_("Settings"), view_name='poll_settings')
@view_action('control_panel_notifications', 'settings',
             title=_("Settings"), view_name='notification_settings')
@view_action('control_panel_agenda_labels', 'agenda_labels',
             title=_("Settings"), view_name='agenda_labels')
def control_panel_link(context, request, va, **kw):
    return """<li><a href="%s">%s</a></li>""" % (
        request.resource_url(request.meeting, va.kwargs['view_name']),
        request.localizer.translate(va.title),
    )


@view_config(context = IMeeting,
             name = "proposal_settings",
             renderer = "arche:templates/form.pt",
             permission = security.MODERATE_MEETING)
class ProposalSettingsForm(ArcheFormCompat, DefaultEditForm):
    type_name = 'Proposal'
    schema_name = 'settings'
    title = _("Proposal settings")


@view_config(context = IMeeting,
             name = "poll_settings",
             renderer = "arche:templates/form.pt",
             permission = security.MODERATE_MEETING)
class PollSettingsForm(ArcheFormCompat, DefaultEditForm):
    type_name = 'Poll'
    schema_name = 'settings'
    title = _("Poll settings")


@view_config(context = IMeeting,
             name = "notification_settings",
             renderer = "arche:templates/form.pt",
             permission = security.MODERATE_MEETING)
class NotificationSettingsForm(ArcheFormCompat, DefaultEditForm):
    type_name = 'Meeting'
    schema_name = 'notification_settings'
    title = _("Notifications")
