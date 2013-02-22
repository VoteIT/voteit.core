import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from betahaus.pyracont.factories import createSchema
from pyramid.renderers import render

from voteit.core.models.access_policy import AccessPolicy
from voteit.core.models.schemas import button_request
from voteit.core.models.schemas import button_cancel
from voteit.core import VoteITMF as _
from voteit.core import security


class ImmediateAP(AccessPolicy):
    """ Grant access for specific permissions immediately if a user requests it.
        No moderator approval requred. This is for very public meetings.
    """
    name = 'public'
    title = _(u"public_access_title",
              default = u"Public access")
    description = _(u"public_access_description",
                    default = u"Users will be granted the permissions you select without prior moderator approval. This is for public meetings.")
    configurable = True

    def view(self, api):
        if not api.userid:
            raise Exception("Can't find userid")
        schema = colander.Schema()
        form = deform.Form(schema, buttons=(button_request, button_cancel,))
        if 'request' in api.request.POST:
            controls = api.request.POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                form_html = e.render()
            #FIXME: Success here
            form_html = "Success, you may now access the meeting"
        else:
            form_html = form.render()

        rolesdict = dict(security.STANDARD_ROLES)

        response = dict(
            api = api,
            form = form_html,
            granted_roles = tuple([rolesdict[x] for x in api.context.get_field_value('immediate_access_grant_roles', [])]),
        )
        return render('templates/request_access_immediate.pt', response, request = api.request)

    def view_submit(self, api):
        roles = self.context.get_field_value('immediate_access_grant_roles')
        self.context.add_groups(api.userid, roles)
        api.flash_messages.add(_(u"Access granted - welcome!"))

    def config_schema(self, api, **kw):
        return createSchema('ImmediateAPConfigSchema')


@schema_factory('ImmediateAPConfigSchema', title = _(u"Configure immediate access policy"))
class ImmediateAPConfigSchema(colander.Schema):
    immediate_access_grant_roles = colander.SchemaNode(
        deform.Set(),
        title = _(u"Roles"),
        description = _(u"immediate_ap_schema_grant_description",
                        default = u"Users will be granted these roles IMMEDIATELY upon requesting access."),
        default = (security.ROLE_VIEWER,),
        widget = deform.widget.CheckboxChoiceWidget(values=security.STANDARD_ROLES,),
    )


def includeme(config):
    config.registry.registerAdapter(ImmediateAP, name = ImmediateAP.name)
