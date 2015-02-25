from __future__ import unicode_literals

from arche.portlets import PortletType
from pyramid.renderers import render
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
import colander
from arche.views.base import BaseView
from betahaus.viewcomponent import render_view_group

from voteit.core.models.interfaces import IMeeting
from voteit.core import _


class MeetingSettingsPortlet(PortletType):
    name = "meeting_settings"
    schema_factory = None
    title = _("Meeting settings")

    def render(self, context, request, view, **kwargs):
        if request.is_moderator and IMeeting.providedBy(context):
            response = {'title': _("Settings"),
                        'portlet': self.portlet,
                        'portlet_cls': "portlet-%s" % self.name,
                        'menu_content': render_view_group(context, request, 'settings_menu', view = view),
                        'view': view,}
            return render("voteit.core:templates/portlets/meeting_actions.pt",
                          response,
                          request = request)


class MeetingMenuPortlet(PortletType):
    """ Various meeting related actions. """

    name = "meeting_various"
    schema_factory = None
    title = _("Meeting various menu")

    def render(self, context, request, view, **kwargs):
        if IMeeting.providedBy(context):
            response = {'title': _("Meeting"),
                        'portlet': self.portlet,
                        'portlet_cls': "portlet-%s" % self.name,
                        'menu_content': render_view_group(context, request, 'meeting', view = view),
                        'view': view,}
            return render("voteit.core:templates/portlets/meeting_actions.pt",
                          response,
                          request = request)


class ParticipantsPortlet(PortletType):
    name = "meeting_participants"
    schema_factory = None
    title = _("Meeting participants")

    def render(self, context, request, view, **kwargs):
        if IMeeting.providedBy(context):
            response = {'title': _("Participants"),
                        'portlet': self.portlet,
                        'portlet_cls': "portlet-%s" % self.name,
                        'menu_content': render_view_group(context, request, 'participants_menu', view = view),
                        'view': view,}
            return render("voteit.core:templates/portlets/meeting_actions.pt",
                          response,
                          request = request)


def includeme(config):
    config.add_portlet(MeetingSettingsPortlet)
    config.add_portlet(MeetingMenuPortlet)
    config.add_portlet(ParticipantsPortlet)
