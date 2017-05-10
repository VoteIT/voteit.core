from arche.interfaces import IRoot
from arche.security import PERM_MANAGE_SYSTEM
from arche.views.base import BaseView
from betahaus.viewcomponent import IViewGroup
from betahaus.viewcomponent import render_view_group
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config

from voteit.core.models.interfaces import IMeeting, IAccessPolicy
from voteit.core.security import VIEW, MODERATE_MEETING


@view_config(context=IRoot,
             permission=NO_PERMISSION_REQUIRED,
             name='_user_menu',
             renderer='voteit.core:templates/snippets/profile_menu.pt')
class MenuView(BaseView):
    """ Generic menu """

    def __call__(self):
        return {}



@view_config(context=IRoot,
             permission=PERM_MANAGE_SYSTEM,
             name='_site_menu',
             renderer='voteit.core:templates/snippets/site_menu.pt')
@view_config(context=IMeeting,
             permission=MODERATE_MEETING,
             name='_site_menu',
             renderer='voteit.core:templates/snippets/site_menu.pt')
class SiteMenuView(BaseView):

    def __call__(self):
        response = {}
        if IMeeting.providedBy(self.context):
            ap = self.request.registry.queryAdapter(self.context, IAccessPolicy,
                                               name=self.context.access_policy)
            response['ap_configurable'] = bool(ap is not None and ap.config_schema())
            response['settings_menu'] = render_view_group(self.context, self.request, 'settings_menu', spacer=" ")
            response['meeting_closed'] = self.context.get_workflow_state() == 'closed'
        return response


@view_config(context=IMeeting,
             permission=VIEW,
             name='_meeting_menu',
             renderer='voteit.core:templates/snippets/meeting_menu.pt')
class MeetingMenuView(BaseView):
    """ Meeting menu"""

    def __call__(self):
        #ap = self.request.registry.queryAdapter(self.context, IAccessPolicy,
        #                                   name=self.context.access_policy)
        response = {}
        #response['ap_configurable'] = bool(ap is not None and ap.config_schema())
        for name in ('meeting_menu', 'participants_menu', 'settings_menu', 'meeting'):
            if self.request.registry.queryUtility(IViewGroup, name):
                response[name] = render_view_group(self.context, self.request, name, spacer=" ")
            else:
                response[name] = ''
        #return render(va.kwargs['renderer'], response, request=request)
        return response