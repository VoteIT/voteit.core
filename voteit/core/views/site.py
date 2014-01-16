import deform
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_save
from voteit.core.models.schemas import button_cancel
from voteit.core.views.base_edit import BaseEdit
from voteit.core import VoteITMF as _


class SiteFormView(BaseEdit):

    @view_config(name="moderators_emails", context=ISiteRoot, renderer="templates/email_list.pt", permission=security.MANAGE_SERVER)
    def moderators_emails(self):
        """ List all moderators emails. """
        userids = set()
        for meeting in self.context.get_content(content_type = 'Meeting', states = ('ongoing', 'upcoming')):
            userids.update(security.find_authorized_userids(meeting, (security.MODERATE_MEETING,)))
        users = []
        for userid in userids:
            user = self.context.users.get(userid, None)
            if user:
                users.append(user)
        def _sorter(obj):
            return obj.get_field_value('email')
        self.response['users'] = tuple(sorted(users, key = _sorter))
        self.response['title'] = _(u"Email addresses of moderators with upcoming or ongoing meetings")
        return self.response

    def form(self, schema_name):
        """ Generic settings for for site root. """
        schema = createSchema(schema_name)
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        form = deform.Form(schema, buttons=(button_save, button_cancel))
        self.api.register_form_resources(form)
        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            updated = self.context.set_field_appstruct(appstruct)
            if updated:
                self.api.flash_messages.add(_(u"Successfully updated"))
            else:
                self.api.flash_messages.add(_(u"Nothing updated"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        #No action - Render form
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = form.render(appstruct)
        return self.response

    @view_config(name = "recaptcha", context=ISiteRoot, renderer = "templates/base_edit.pt", permission = security.EDIT)
    def recaptcha(self):
        return self.form("CaptchaSiteRootSchema")

    @view_config(name = "layout", context = ISiteRoot, permission = security.EDIT, renderer = "templates/base_edit.pt")
    def layout(self):
        return self.form("LayoutSiteRootSchema")
