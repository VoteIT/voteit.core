from betahaus.pyracont.factories import createSchema
from deform import Form
from deform.exception import ValidationFailure
from pyramid.url import resource_url
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.schemas import add_csrf_token
from voteit.core.security import MANAGE_GROUPS


class PermissionsView(BaseView):
    """ View for setting permissions """

    @view_config(context=IMeeting, name="permissions", renderer="templates/base_edit.pt", permission=MANAGE_GROUPS)
    @view_config(context=ISiteRoot, name="permissions", renderer="templates/base_edit.pt", permission=MANAGE_GROUPS)
    def meeting_group_form(self):
        post = self.request.POST
        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        schema = createSchema('PermissionsSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)

        form = Form(schema, buttons=('save', 'cancel'))
        self.api.register_form_resources(form)

        if 'save' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            #Set permissions
            self.context.set_security(appstruct['userids_and_groups'])
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        appstruct = dict(
            userids_and_groups = self.context.get_security()
        )

        self.response['form'] = form.render(appstruct=appstruct)
        return self.response
