from arche.security import groupfinder
from arche.views.base import BaseView
from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import view_config
from pyramid.view import view_defaults

from voteit.core import security
from voteit.core.fanstaticlib import participants_js
from voteit.core.helpers import get_meeting_participants
from voteit.core.models.interfaces import IMeeting
from voteit.core.security import MODERATE_MEETING


_VIEW_ROLES = (('role_view', security.ROLE_VIEWER),
               ('role_discuss', security.ROLE_DISCUSS),
               ('role_propose', security.ROLE_PROPOSE),
               ('role_vote', security.ROLE_VOTER),
               ('role_moderate', security.ROLE_MODERATOR),
               ('role_admin', security.ROLE_ADMIN),)


#Only allow VoteIT core roles
_ALLOWED_TO_TOGGLE = (security.ROLE_VIEWER,
                      security.ROLE_DISCUSS,
                      security.ROLE_PROPOSE,
                      security.ROLE_VOTER,
                      security.ROLE_MODERATOR)


#glyphicon glyphicon + ->
_ROLE_ICONS = {'role_view': 'eye-open',
               'role_discuss': 'comment',
               'role_propose': 'exclamation-sign',
               'role_vote': 'star',
               'role_moderate': 'king',
               'role_admin': 'cog'}


@view_defaults(context = IMeeting, permission = security.VIEW)
class ParticipantsView(BaseView):

    @view_config(name = 'participants', renderer = 'voteit.core:templates/participants.pt')
    def main(self):
        participants_js.need()
        response = {}
        #This might be slow in its current form. Make get_meeting_participants smarter
        response['participants_count'] = len(get_meeting_participants(self.context))
        response['view_roles'] = _VIEW_ROLES
        response['role_icons'] = _ROLE_ICONS
        response['meeting_closed'] = self.context.get_workflow_state() == 'closed'
        return response

    @view_config(name = 'participants.json', renderer = 'json')
    def json_data(self):
        users = self.root['users']
        results = []
        userids = get_meeting_participants(self.context)
        query = "userid in any(%s)" % list(userids)
        role_count = {}
        for key in dict(_VIEW_ROLES).keys():
            role_count[key] = 0
        for user in self.catalog_query(query, resolve = True, perm = None, sort_index = 'sortable_title'):
            uroles = groupfinder(user.userid, self.request)
            userdata = {'first_name': user.first_name,
                        'last_name': user.last_name,
                        'userid': user.userid,}
            if self.request.is_moderator:
                userdata['email'] = user.email
            for (name, role) in _VIEW_ROLES:
                userdata[name] = role in uroles
                if role in uroles:
                   role_count[name] += 1
            results.append(userdata)
        return {'results': results,
                'moderator': bool(self.request.is_moderator),
                'role_count': role_count}

    @view_config(name = '_toggle_participant_role',
                 renderer = 'json',
                 permission = MODERATE_MEETING,
                 xhr = True)
    def toggle_participant_role(self):
        userid = self.request.POST.get('userid', '')
        view_roles = dict(_VIEW_ROLES)
        view_name_role = self.request.POST.get('role', '')
        role = view_roles.get(view_name_role, None)
        if role not in _ALLOWED_TO_TOGGLE:
            raise HTTPForbidden("Not allowed to tinker with role: '%s'" % view_name_role)
        enabled = self.request.POST.get('enabled', None)
        enabled = {'1': True, '0': False}.get(enabled, None)
        if enabled not in (True, False):
            raise HTTPForbidden("'enabled' must be '1' or '0'")
        #Toggle, so if a user has a role remove it
        if enabled:
            status = False
            self.context.local_roles.remove(userid, role)
        else:
            status = True
            self.context.local_roles.add(userid, role)
        return {'role': view_name_role,
                'userid': userid,
                'status': status}
