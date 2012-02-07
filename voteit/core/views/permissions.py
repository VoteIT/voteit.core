from betahaus.pyracont.factories import createSchema
from deform import Form
from deform.exception import ValidationFailure
from pyramid.url import resource_url
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.schemas import add_csrf_token
from voteit.core import security


class PermissionsView(BaseView):
    """ View for setting permissions """

    @view_config(context=ISiteRoot, name="permissions", renderer="templates/permissions.pt", permission=security.MANAGE_GROUPS)
    @view_config(context=IMeeting, name="permissions", renderer="templates/permissions.pt", permission=security.MANAGE_GROUPS)
    def group_form(self):
        if IMeeting.providedBy(self.context):
            self.response['title'] = _(u"Edit permissions")
        else:
            self.response['title'] = _(u"Root permissions")

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

        userids_and_groups = self.context.get_security()
        #Update with full name as well
        for entry in userids_and_groups:
            userid = entry['userid']
            user = self.api.get_user(userid)
            if user is None:
                continue
            entry['name'] = "%s %s".strip() % (user.get_field_value('first_name'), user.get_field_value('last_name'))

        #No action - Render edit form
        appstruct = dict( userids_and_groups = userids_and_groups )

        self.response['form'] = form.render(appstruct=appstruct)
        return self.response
    
    @view_config(context=ISiteRoot, name="add_permission", renderer="templates/base_edit.pt", permission=security.MANAGE_GROUPS)
    @view_config(context=IMeeting, name="add_permission", renderer="templates/base_edit.pt", permission=security.MANAGE_GROUPS)
    def add_permission(self):
        if IMeeting.providedBy(self.context):
            self.response['title'] = _(u"Add participant")
        else:
            self.response['title'] = _(u"Add permission")

        post = self.request.POST
        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        schema = createSchema('SingelPermissionSchema').bind(context=self.context, request=self.request)
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
            self.context.set_groups(appstruct['userid'], appstruct['groups'])
            msg = _(u"Added permssion for user ${userid}", mapping={'userid':appstruct['userid']} )
            self.api.flash_messages.add(msg)
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        self.response['form'] = form.render()
        return self.response