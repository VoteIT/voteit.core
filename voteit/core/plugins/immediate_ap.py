from __future__ import unicode_literals

import colander
import deform
from pyramid.httpexceptions import HTTPFound

from voteit.core.models.access_policy import AccessPolicy
from voteit.core import VoteITMF as _
from voteit.core import security


class ImmediateAP(AccessPolicy):
    """ Grant access for specific permissions immediately if a user requests it.
        No moderator approval requred. This is for very public meetings.
    """
    name = 'public'
    title = _("Public access")
    description = _("public_access_description",
                    default = "Users will be granted the permissions you select without prior moderator approval. This is for public meetings.")

    def schema(self):
        return colander.Schema(title = _("Would you like to participate?"),
                               description = _("Clicking request access will grant you access right away!"))

    def handle_success(self, view, appstruct):
        rolesdict = dict(security.STANDARD_ROLES)
        roles = self.context.get_field_value('immediate_access_grant_roles')
        self.context.add_groups(view.request.authenticated_userid, roles)
        view.flash_messages.add(_("Access granted - welcome!"))
        return HTTPFound(location = view.request.resource_url(self.context))

    def config_schema(self):
        return ImmediateAPConfigSchema()


class ImmediateAPConfigSchema(colander.Schema):
    title = _("Configure immediate access policy")
    immediate_access_grant_roles = colander.SchemaNode(
        colander.Set(),
        title = _("Roles"),
        description = _("immediate_ap_schema_grant_description",
                        default = "Users will be granted these roles IMMEDIATELY upon requesting access."),
        default = (security.ROLE_VIEWER,),
        widget = deform.widget.CheckboxChoiceWidget(values=security.STANDARD_ROLES,),
    )


def includeme(config):
    config.registry.registerAdapter(ImmediateAP, name = ImmediateAP.name)
