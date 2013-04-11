import deform
from deform import Form
from deform.exception import ValidationFailure
from pyramid.security import has_permission
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.url import resource_url
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_save
from voteit.core.models.schemas import button_cancel


class MeetingView(BaseView):
    
    @view_config(context=IMeeting, renderer="templates/base_view.pt", permission = NO_PERMISSION_REQUIRED)
    def meeting_view(self):
        """ Meeting view behaves a bit differently than regular views since
            it should allow users to request access if unauthorized is raised.
        """
        if not has_permission(security.VIEW, self.context, self.request):
            #We delegate permission checks to the request_meeting_access part.
            url = self.request.resource_url(self.context, 'request_access')
            return HTTPFound(location = url)
        return self.response

    @view_config(name="participants_emails", context=IMeeting, renderer="templates/email_list.pt", permission=security.MODERATE_MEETING)
    def participants_emails(self):
        """ List all participants emails in this meeting. """
        users = self.api.root.users
        results = []
        for userid in security.find_authorized_userids(self.context, (security.VIEW,)):
            user = users.get(userid, None)
            if user:
                results.append(user)
        def _sorter(obj):
            return obj.get_field_value('email')
        self.response['users'] = tuple(sorted(results, key = _sorter))
        self.response['title'] = _(u"Email addresses of participants")
        return self.response

    @view_config(name="manage_layout", context=IMeeting, renderer="templates/base_edit.pt", permission=security.EDIT)
    def manage_layout(self):
        """ Manage layout
        """
        self.response['title'] = _(u"Layout")

        schema = createSchema('LayoutSchema')
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api=self.api)
            
        form = Form(schema, buttons=(button_save, button_cancel,))
        self.api.register_form_resources(form)

        post = self.request.POST

        if 'save' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            self.context.set_field_appstruct(appstruct)
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render form
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = form.render(appstruct)
        return self.response

    @view_config(name = 'request_access', context = IMeeting,
                 renderer = "templates/request_meeting_access.pt", permission = NO_PERMISSION_REQUIRED)
    def request_meeting_access(self):
        #If user already has permissions redirect to main meeting view
        if has_permission(security.VIEW, self.context, self.request):
            url = resource_url(self.context, self.request)
            return HTTPFound(location = url)
        if not self.api.userid:
            msg = _('request_access_view_login_register',
                    default=u"You need to login or register before you can use any meetings.")
            self.api.flash_messages.add(msg, type='info')
            came_from = resource_url(self.context, self.request, 'request_access')
            url = self.request.resource_url(self.api.root, query={'came_from': came_from})
            return HTTPFound(location = url)

        access_policy_name = self.context.get_field_value('access_policy', 'invite_only')
        access_policy = self.request.registry.queryAdapter(self.context, IAccessPolicy, name = access_policy_name)
        if access_policy and 'request' in self.request.POST:
            access_policy.view_submit(self.api)
            return HTTPFound(location = self.api.meeting_url)

        self.response['access_policy'] = access_policy
        if access_policy is None:
            err_msg = _(u"access_policy_not_found",
                        default = u"""Can't find an access policy with the id '${policy}'.
                                    This might mean that the registered access type for this meeting doesn't exist anylonger.
                                    Please contact the moderator about this.""",
                        mapping = {'policy': access_policy_name})
            self.api.flash_messages.add(err_msg, type="error")
            self.response['form'] = u''
        else:
            self.response['form'] = access_policy.view(self.api)
        return self.response

    @view_config(context=IMeeting, name="configure_access_policy", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def configure_access_policy(self):
        access_policy_name = self.context.get_field_value('access_policy', 'invite_only')
        access_policy = self.request.registry.queryAdapter(self.context, IAccessPolicy, name = access_policy_name)
        if not access_policy:
            err_msg = _(u"access_policy_not_found_moderator",
                        default = u"""Can't find an access policy with the id '${policy}'.
                                    This might mean that the registered access type for this meeting doesn't exist anylonger.
                                    Please change access policy.""",
                        mapping = {'policy': access_policy_name})
            self.api.flash_messages.add(err_msg, type="error")
            url = self.request.resource_url(self.api.meeting, 'access_policy')
            return HTTPFound(location=url)
        
        schema = access_policy.config_schema(self.api)
        form = access_policy.config_form(schema)
        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            form = access_policy.config_form(schema)
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            self.context.set_field_appstruct(appstruct)
            #FIXME: Flash: saved
            url = self.request.resource_url(self.api.meeting)
            return HTTPFound(location=url)
        else:
            #Render normal form
            appstruct = self.context.get_field_appstruct(schema)
            self.response['form'] = form.render(appstruct = appstruct)
            return self.response

    @view_config(context=IMeeting, name="presentation", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def presentation(self):
        schema = createSchema("PresentationMeetingSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        return self.form(schema)
    
    @view_config(context=IMeeting, name="mail_settings", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def mail_settings(self):
        schema = createSchema("MailSettingsMeetingSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        return self.form(schema)
        
    @view_config(context=IMeeting, name="access_policy", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def access_policy(self):
        schema = createSchema("AccessPolicyMeetingSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        result = self.form(schema)
        if 'save' in self.request.POST:
            ap = self.request.registry.queryAdapter(self.context, IAccessPolicy, name = self.context.get_field_value('access_policy', ''))
            if ap and ap.configurable:
                self.api.flash_messages.add(_(u"Review access policy configuration"))
                url = self.request.resource_url(self.context, 'configure_access_policy')
                return HTTPFound(location = url)
        return result

    @view_config(context=IMeeting, name="meeting_poll_settings", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def global_poll_settings(self):
        schema = createSchema("MeetingPollSettingsSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        return self.form(schema)

    @view_config(context=IMeeting, name="mail_notification_settings", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def mail_notification_settings(self):
        schema = createSchema("MailNotificationSettingsSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        return self.form(schema)

    def form(self, schema):
        form = Form(schema, buttons=(button_save, button_cancel))
        self.api.register_form_resources(form)
        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response

            updated = self.context.set_field_appstruct(appstruct)
            if updated:
                self.api.flash_messages.add(_(u"Successfully updated"))
            else:
                self.api.flash_messages.add(_(u"Nothing updated"))                
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render form
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = form.render(appstruct)
        return self.response

    @view_config(context = IMeeting, name = "minutes", renderer = "templates/minutes.pt", permission = security.VIEW)
    def minutes(self):
        """ Show an overview of the meeting activities. Should work as a template for minutes. """

        if self.api.meeting.get_workflow_state() != 'closed':
            msg = _(u"meeting_not_closed_minutes_incomplete_notice",
                    default = u"This meeting hasn't closed yet so these minutes won't be complete")
            self.api.flash_messages.add(msg)
        #Add agenda item objects to response
        agenda_items = []
        query = dict(
            context = self.context,
            content_type = "AgendaItem",
            workflow_state = ('upcoming', 'ongoing', 'closed'),
            sort_index = "order",
        )
        for docid in self.api.search_catalog(**query)[1]:
            agenda_items.append(self.api.resolve_catalog_docid(docid))

        self.response['agenda_items'] = agenda_items
        return self.response
