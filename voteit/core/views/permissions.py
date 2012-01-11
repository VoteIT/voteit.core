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
from voteit.core import security
from voteit.core.fanstaticlib import voteit_deform


class PermissionsView(BaseView):
    """ View for setting permissions """

    @view_config(context=ISiteRoot, name="permissions", renderer="templates/permissions.pt", permission=security.MANAGE_GROUPS)
    @view_config(context=IMeeting, name="permissions", renderer="templates/permissions.pt", permission=security.MANAGE_GROUPS)
    def root_group_form(self):
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

    def meeting_group_form(self):
        voteit_deform.need()
        
        post = self.request.POST
        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'save' in post:
            userids_and_groups = []
            controls = post.items()
            for control in controls:
                if '__start__' in control[0]:
                    userid = control[1]
                    groups = []
                if userid == 'new' and 'userid' in control[0]:
                    userid = control[1]
                if 'group' in control[0]:
                    groups.append(control[1])
                if '__end__' in control[0]:
                    userids_and_groups.append({'userid': userid, 'groups': set(groups)})

            #Set permissions
            self.context.set_security(userids_and_groups)
            url = self.request.path_url
            return HTTPFound(location=url)

        #No action - Render edit form
        
        users = self.api.root.users
        
        results = []
        for userid in security.find_authorized_userids(self.context, (security.VIEW,)):
            user = users.get(userid, None)
            if user:
                results.append(user)
        
        def _sorter(obj):
            return obj.get_field_value('first_name')

        #Viewer role isn't needed, since only users who can view will be listed here.
        self.response['roles'] = security.MEETING_ROLES
        self.response['participants'] = tuple(sorted(results, key = _sorter))
        self.response['context_effective_principals'] = security.context_effective_principals
        self.response['autocomplete_userids'] = '"' + '","'.join(self.api.root.users.keys()) + '"'
        return self.response
