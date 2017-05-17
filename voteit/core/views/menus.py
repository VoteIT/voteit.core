from arche.interfaces import IRoot
from arche.security import PERM_MANAGE_SYSTEM
from arche.views.base import BaseView
from betahaus.viewcomponent import IViewGroup
from betahaus.viewcomponent import render_view_group
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPUnauthorized
from voteit.core.helpers import get_polls_struct

from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPoll
from voteit.core.security import ADD_VOTE
from voteit.core.security import MODERATE_MEETING
from voteit.core.security import VIEW


@view_config(context=IRoot,
             permission=VIEW,
             name='_user_menu',
             renderer='voteit.core:templates/snippets/profile_menu.pt')
class MenuView(BaseView):
    """ Generic menu """

    def __call__(self):
        if not self.request.authenticated_userid:
            raise HTTPUnauthorized("Must login first")
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
            ap_name = self.context.access_policy
            if not ap_name:
                ap_name = 'invite_only'
            ap = self.request.registry.queryAdapter(self.context, IAccessPolicy,
                                               name=ap_name)
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
        response = {}
        for name in ('meeting_menu', 'participants_menu', 'meeting'):
            if self.request.registry.queryUtility(IViewGroup, name):
                response[name] = render_view_group(self.context, self.request, name, spacer=" ")
            else:
                response[name] = ''
        return response


@view_config(context=IMeeting,
             permission=VIEW,
             name='_poll_menu',
             renderer='voteit.core:templates/snippets/poll_menu.pt')
class PollMenuView(BaseView):
    """ Poll menu"""

    def __call__(self):
        response = {}
        response['state_titles'] = self.request.get_wf_state_titles(IPoll, 'Poll')
        response['polls_structure'] = get_polls_struct(self.context, self.request, limit = 5)
        response['vote_perm'] = ADD_VOTE
        response['only_link'] = self.context.polls_menu_only_links
        return response
