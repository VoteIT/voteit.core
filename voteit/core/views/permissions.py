from arche import _ as arche_mf
from arche.interfaces import ILocalRoles
from arche.security import PERM_MANAGE_USERS
from arche.views.actions import actionbar_main_generic
from arche.views.base import BaseForm
from betahaus.viewcomponent.decorators import view_action
from deform import Button
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from voteit.core import _
from voteit.core import security
from voteit.core.models.interfaces import IMeeting


@view_action('actionbar_main', 'permissions',
             title = arche_mf("Permissions"),
             view_name = 'permissions',
             permission = PERM_MANAGE_USERS, #Same perm as Arche
             priority = 40)
def permissions_action(context, request, va, **kw):
    """ Override regular permission button in the action bar. It shouldn't be used within meetings.
    """
    if not request.meeting and ILocalRoles.providedBy(context):
        return actionbar_main_generic(context, request, va, **kw)

#Should we block perms for all contexts within a meeting?

#FIXME: Proper permissions view

@view_config(context = IMeeting,
             permission = security.MODERATE_MEETING,
             name = "add_userid",
             renderer = "voteit.core:templates/participants_form.pt")
class AddExistingUserForm(BaseForm):
    title = _("Add existing user to meeting")
    schema_name = 'add_existing_user'
    type_name = 'Meeting'

    @property
    def buttons(self):
        return (self.button_add, self.button_cancel)

    def add_success(self, appstruct):
        userid = appstruct['userid']
        roles = appstruct['roles']
        if roles and security.ROLE_VIEWER not in roles:
            roles.add(security.ROLE_VIEWER)
        old_roles = self.context.local_roles.get(userid, set())
        if old_roles:
            new_roles = roles - old_roles
            if new_roles:
                trans = self.request.localizer.translate
                role_titles = []
                for role_name in new_roles:
                    role = self.request.registry.roles.get(role_name)
                    role_titles.append(trans(role.title))
                msg = _("new_roles_appended_notice",
                        default = "User was already a part of this meeting, "
                        "but these new roles were added: ${roles}",
                        mapping = {'roles': ", ".join(role_titles)})
                self.flash_messages.add(msg, type = 'warning')
            else:
                self.flash_messages.add(_("No new roles added - user already had all of them."))
        else:
            #Userid wasn't registered in this meeting
            self.flash_messages.add(self.default_success, type = "success")
        self.context.local_roles.add(appstruct['userid'], roles)
        return HTTPFound(location = self.request.resource_url(self.context, 'add_userid'))
