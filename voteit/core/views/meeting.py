import deform
from colander import Schema
from deform import Form
from deform.exception import ValidationFailure
from pyramid.security import has_permission
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPRedirection
from pyramid.url import resource_url
from betahaus.pyracont.factories import createSchema
from betahaus.viewcomponent.interfaces import IViewGroup

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
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
            url = resource_url(self.context, self.request) + 'request_access'
            return HTTPFound(location = url)
        
        return self.response

    @view_config(name="participants_emails", context=IMeeting, renderer="templates/participants_emails.pt", permission=security.MODERATE_MEETING)
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

        self.response['participants'] = tuple(sorted(results, key = _sorter))
        return self.response

    @view_config(name="manage_layout", context=IMeeting, renderer="templates/base_edit.pt", permission=security.EDIT)
    def manage_layout(self):
        """ Manage layout
        """
        self.response['title'] = _(u"Layout")

        schema = createSchema('LayoutSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)
            
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
        
        access_policy = self.context.get_field_value('access_policy', 'invite_only')
        
        # show log in/register view if user is not logged in and access policy is no invite only
        if not self.api.userid and not access_policy == 'invite_only':
            msg = _('request_access_view_login_register',
                    default=u"""This meeting requires the participants to be logged in. If you are 
                    registered please log in or register an account here. You will be returned to the 
                    meeting afterwards""")
            self.api.flash_messages.add(msg, type='info')
            came_from = resource_url(self.context, self.request, 'request_access')
            url = resource_url(self.api.root, self.request, 'login', query={'came_from': came_from})
            schema = Schema()
            form = Form(schema, buttons=(deform.Button('login_register', _(u"Login/Register")),), action=url)
            self.api.register_form_resources(form)
            self.response['form'] = form.render()
            return self.response 
        
        view_group = self.request.registry.getUtility(IViewGroup, name = 'request_meeting_access')        
        va = view_group.get(access_policy, None)
        if va is None:
            err_msg = _(u"request_access_view_action_not_found",
                        default = u"Can't find an action associated with access policy ${policy}.",
                        mapping = {'policy': access_policy})
            self.api.flash_messages.add(err_msg, type="error")
            url = resource_url(self.api.root, self.request)
            return HTTPFound(location=url)
        result = va(self.context, self.request, api = self.api)
        if isinstance(result, HTTPRedirection):
            return result
        self.response['form'] = result
        return self.response

    @view_config(context=IMeeting, name="presentation", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def presentation(self):
        schema = createSchema("PresentationMeetingSchema").bind(context=self.context, request=self.request)
        return self.form(schema)
    
    @view_config(context=IMeeting, name="mail_settings", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def mail_settings(self):
        schema = createSchema("MailSettingsMeetingSchema").bind(context=self.context, request=self.request)
        return self.form(schema)
        
    @view_config(context=IMeeting, name="access_policy", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def access_policy(self):
        schema = createSchema("AccessPolicyMeetingSchema").bind(context=self.context, request=self.request)
        return self.form(schema)

    @view_config(context=IMeeting, name="meeting_poll_settings", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def global_poll_settings(self):
        schema = createSchema("MeetingPollSettingsSchema").bind(context=self.context, request=self.request)
        return self.form(schema)

    def form(self, schema):
        add_csrf_token(self.context, self.request, schema)
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
