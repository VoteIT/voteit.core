from arche.interfaces import IRoot
from arche.security import PERM_MANAGE_SYSTEM
from arche.views.base import BaseView
from betahaus.viewcomponent import IViewGroup
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPUnauthorized

from voteit.core.helpers import get_polls_struct
from voteit.core.helpers import ROLE_ICONS
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPoll
from voteit.core.security import ADD_VOTE
from voteit.core.security import VIEW


@view_config(context=IRoot,
             permission=VIEW,
             name='_user_menu',
             renderer='voteit.core:templates/menus/profile.pt')
@view_config(context=IMeeting,
             permission=VIEW,
             name='_user_menu',
             renderer='voteit.core:templates/menus/profile.pt')
class MenuView(BaseView):
    """ Generic menu """

    def __call__(self):
        if not self.request.authenticated_userid:
            raise HTTPUnauthorized("Must login first")
        show_roles = IMeeting.providedBy(self.context)
        local_roles = []
        if show_roles:
            for role in self.context.local_roles.get(self.request.authenticated_userid, ()):
                local_roles.append(self.request.registry.roles[role])
        return {'show_roles': show_roles,
                'local_roles': local_roles,
                'role_icons': ROLE_ICONS}


@view_config(context=IRoot,
             permission=PERM_MANAGE_SYSTEM,
             name='_site_menu',
             renderer='voteit.core:templates/menus/site.pt')
class SiteMenuView(BaseView):

    def __call__(self):
        return {}


@view_config(context=IMeeting,
             permission=VIEW,
             name='_control_panel',
             renderer='voteit.core:templates/menus/control_panel.pt')
class ControlPanelView(BaseView):

    def __call__(self):
        response = {}
        control_panels = self.request.registry.getUtility(IViewGroup, name = 'control_panel')
        response['control_panels_active'] = control_panels(self.context, self.request, as_type='generator', active=True)
        response['control_panels_inactive'] = control_panels(self.context, self.request, as_type='list', active=False)
        return response


@view_config(context=IMeeting,
             permission=VIEW,
             name='_poll_menu',
             renderer='voteit.core:templates/menus/poll.pt')
class PollMenuView(BaseView):
    """ Poll menu"""

    def __call__(self):
        response = {}
        response['state_titles'] = self.request.get_wf_state_titles(IPoll, 'Poll')
        response['polls_structure'] = get_polls_struct(self.context, self.request, limit = 5)
        response['vote_perm'] = ADD_VOTE
        response['only_link'] = self.context.polls_menu_only_links
        return response
