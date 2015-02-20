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
            response = {'title': self.title,
                        'portlet': self.portlet,
                        'settings_content': render_view_group(context, request, 'settings_menu', view = view),
                        'view': view,}
            return render("voteit.core:templates/portlets/meeting_settings.pt",
                          response,
                          request = request)


def includeme(config):
    config.add_portlet(MeetingSettingsPortlet)
