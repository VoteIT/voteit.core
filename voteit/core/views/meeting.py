import deform
from deform import Form
from deform.exception import ValidationFailure
from pyramid.security import has_permission
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.traversal import resource_path
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from betahaus.pyracont.factories import createSchema
from repoze.catalog.query import Eq

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_save
from voteit.core.models.schemas import button_cancel
from voteit.core.views.base_edit import DefaultEditForm


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

    @view_config(name = 'request_access', context = IMeeting,
                 renderer = "templates/request_meeting_access.pt", permission = NO_PERMISSION_REQUIRED)
    def request_meeting_access(self):
        """ This page appears when a user clicked on a link to a meeting where the user in question
            don't have access.
            This is controled via access policies. See IAccessPolicy
        """
        #If user already has permissions redirect to main meeting view
        if has_permission(security.VIEW, self.context, self.request):
            return HTTPFound(location = self.request.resource_url(self.context))
        if not self.api.userid:
            msg = _('request_access_view_login_register',
                    default=u"You need to login or register before you can use any meetings.")
            self.api.flash_messages.add(msg, type='info')
            came_from = self.request.resource_url(self.context, 'request_access')
            url = self.request.resource_url(self.api.root, query={'came_from': came_from})
            return HTTPFound(location = url)
        access_policy_name = self.context.get_field_value('access_policy', 'invite_only')
        access_policy = self.request.registry.queryAdapter(self.context, IAccessPolicy, name = access_policy_name)
        #Did we find a valid access policy for this meeting?
        if not access_policy:
            err_msg = _(u"access_policy_not_found",
                        default = u"""Can't find an access policy with the id '${policy}'.
                                    This might mean that the registered access type for this meeting doesn't exist anylonger.
                                    Please contact the moderator about this.""",
                        mapping = {'policy': access_policy_name})
            self.api.flash_messages.add(err_msg, type="error")
            return HTTPFound(location = self.request.application_url)
        #Does this policy implement its own view?
        if access_policy.view:
            result = access_policy.render_view(self.api)
            if isinstance(result, dict) or isinstance(result, Response):
                return result
            return Response(result)
        #This policy probably just defines a custom schema or a custom form
        form = access_policy.form(self.api)
        if 'request_access' in self.request.POST:
            controls = self.request.POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            access_policy.handle_success(self.api, appstruct)        
            url = self.request.resource_url(self.api.meeting)
            return HTTPFound(location = url)
        if 'cancel' in self.request.POST:
            return HTTPFound(location = self.request.application_url)
        self.response['form'] = form.render()
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
        form = access_policy.config_form(self.api)
        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            self.context.set_field_appstruct(appstruct)
            self.api.flash_messages.add(_(u"Saved"))
            url = self.request.resource_url(self.api.meeting)
            return HTTPFound(location=url)
        #Render normal form
        schema = access_policy.config_schema(self.api)
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = form.render(appstruct = appstruct)
        return self.response

    @view_config(context=IMeeting, name="presentation", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def presentation(self):
        schema = createSchema("PresentationMeetingSchema")
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


@view_config(name = "reload_data.json", context = IMeeting, permission = security.VIEW, renderer = 'json')
def reload_data_json(context, request):
    """ A json list of things interesting for an eventual update of agenda items view or poll menu.
        See reload_meeting_data in voteit_common.js
    
        Note: This is not a smart way of doing this, so MAKE SURE this executes fast!
        This will be replaced when proper websockets are in place.
    """
    root = context.__parent__
    response = {'polls': {}, 'proposals': {}, 'discussionposts': ()}
    #Get poll reload information
    query = Eq('content_type', 'Poll' ) & Eq('path', resource_path(context))
    #ISn't there a smarter way to load wfs?
    for wf_state in ('upcoming', 'ongoing', 'canceled', 'closed'):
        response['polls'][wf_state] = tuple(root.catalog.query(query & Eq('workflow_state', wf_state),
                                                               sort_index = 'created')[1])
    #Fetch proposals and discussions? We'll focus on unread here, polls should catch wf changes on most proposals
    ai_name = request.GET.get('ai_name', None)
    if ai_name and ai_name in context:
        query = Eq('path', resource_path(context, ai_name))
        #Proposal
        #This seems silly too...
        for wf_state in ('published', 'retracted', 'voting', 'approved', 'denied', 'unhandled'):
            response['proposals'][wf_state] = tuple(root.catalog.query(query & Eq('content_type', 'Proposal') \
                                                                       & Eq('workflow_state', wf_state),
                                                                       sort_index = 'created')[1])
        #DiscussionPost
        response['discussionposts'] = tuple(root.catalog.query(query & Eq('content_type', 'DiscussionPost'),
                                                               sort_index = 'created')[1])
    return response


@view_config(context = IMeeting,
             name = "mail_settings",
             renderer = "voteit.core:views/templates/base_edit.pt",
             permission = security.MODERATE_MEETING)
class MailSettingsForm(DefaultEditForm):

    def get_schema(self):
        return createSchema("MailSettingsMeetingSchema")


@view_config(context = IMeeting,
             name = "access_policy",
             renderer = "voteit.core:views/templates/base_edit.pt",
             permission = security.MODERATE_MEETING)
class AccessPolicyForm(DefaultEditForm):

    def get_schema(self):
        return createSchema("AccessPolicyMeetingSchema")

    def save_success(self, appstruct):
        response = super(AccessPolicyForm, self).save_success(appstruct)
        ap = self.request.registry.queryAdapter(self.context,
                                                IAccessPolicy,
                                                name = self.context.get_field_value('access_policy', ''))
        if ap and ap.configurable:
            self.api.flash_messages.add(_(u"Review access policy configuration"))
            url = self.request.resource_url(self.context, 'configure_access_policy')
            return HTTPFound(location = url)
        return response


@view_config(context = IMeeting,
             name = "meeting_poll_settings",
             renderer = "voteit.core:views/templates/base_edit.pt",
             permission = security.MODERATE_MEETING)
class MeetingPollSettingsForm(DefaultEditForm):

    def get_schema(self):
        return createSchema("MeetingPollSettingsSchema")
