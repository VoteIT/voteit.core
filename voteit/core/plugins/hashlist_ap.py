from __future__ import unicode_literals

import colander
import deform
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.threadlocal import get_current_request
from repoze.catalog.query import Eq

from voteit.core import _
from voteit.core import security
from voteit.core.models.access_policy import AccessPolicy


class HashlistAP(AccessPolicy):
    """ Grant access for specific permissions immediately if a user requests it
        and that users email is registered within a specific hashlist.
        No moderator approval requred.
    """
    name = 'hashlist'
    title = _("Hashlist access")
    description = _(
        "hashlist_access_description",
        default="Users will be granted the permissions you select without"
                "prior moderator approval if their email is registered "
                "within a hashlist. arche_hashlist must be installed for "
                "this to work."
    )

    @reify
    def hashlist(self):
        request = get_current_request()
        ap_hashlist_uid = self.context.get_field_value('ap_hashlist_uid', '')
        hashlist = request.resolve_uid(ap_hashlist_uid, perm=None)
        if not hashlist:
            raise HTTPForbidden(_("Access policy isn't configured correctly"))
        return hashlist

    def schema(self):
        #Just to make sure
        self.hashlist
        return colander.Schema(
            title=_("Would you like to participate?"),
            description=_(
                "Clicking request access will grant you access if your email address"
                "is allowed by the access policy."
            )
        )

    def handle_success(self, view, appstruct):
        # Check
        profile = view.request.profile
        if not profile:
            raise HTTPUnauthorized("No profile found")
        if not profile.email_validated:
            raise HTTPForbidden(_("Your email isn't validated. Check your profile menu."))
        if not self.hashlist.check(profile.email):
            msg = _("email_address_not_listed_as_allowed",
                    default="Your email address isn't listed as allowed to access this meeting."
                            "Contact the moderator to request access."
                    )
            raise HTTPForbidden(msg)
        roles = self.context.get_field_value('immediate_access_grant_roles')
        self.context.add_groups(view.request.authenticated_userid, roles)
        view.flash_messages.add(_("Access granted - welcome!"))
        return HTTPFound(location=view.request.resource_url(self.context))

    def config_schema(self):
        return HashlistAPConfigSchema()


@colander.deferred
def ap_hashlist_uid_widget(node, kw):
    request = kw['request']
    query = Eq('type_name', 'HashList')
    docids = request.root.catalog.query(query)[1]
    values = [('', _("<Select>"))]
    for obj in request.resolve_docids(docids):
        values.append((obj.uid, obj.title))
    return deform.widget.SelectWidget(values=values)


class HashlistAPConfigSchema(colander.Schema):
    title = _("Configure access policy")
    description = _("Access will be granted if users are present in the hashlist.")
    ap_hashlist_uid = colander.SchemaNode(
        colander.String(),
        title=_("Hashlist"),
        description=_("ap_hashlist_uid_description",
                      default="If nothing is present here, it might mean that you "
                              "don't have permission to see any hashlists, "
                              "or that arche_hashlist isn't installed."),
        widget=ap_hashlist_uid_widget,
    )
    immediate_access_grant_roles = colander.SchemaNode(
        colander.Set(),
        title=_("Roles"),
        description=_("immediate_ap_schema_grant_description",
                      default="Users will be granted these roles upon requesting access and passing check."),
        default=(security.ROLE_VIEWER,),
        widget=deform.widget.CheckboxChoiceWidget(values=security.STANDARD_ROLES, ),
    )


def includeme(config):
    config.registry.registerAdapter(HashlistAP, name=HashlistAP.name)
