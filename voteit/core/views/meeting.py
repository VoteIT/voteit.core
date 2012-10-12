import urllib

from deform import Form
from deform.exception import ValidationFailure
from pyramid.security import has_permission
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPRedirection
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.url import resource_url
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema
from betahaus.viewcomponent.interfaces import IViewGroup
from repoze.workflow.workflow import WorkflowError


from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.agenda_item import AgendaItem
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_save
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_resend
from voteit.core.models.schemas import button_delete
from voteit.core.validators import deferred_token_form_validator
from voteit.core.helpers import ajax_options
from voteit.core import fanstaticlib


class MeetingView(BaseView):
    
    @view_config(context=IMeeting, renderer="templates/meeting.pt", permission = NO_PERMISSION_REQUIRED)
    def meeting_view(self):
        """ Meeting view behaves a bit differently than regular views since
            it should allow users to request access if unauthorized is raised.
        """
        if not has_permission(security.VIEW, self.context, self.request):
            #We delegate permission checks to the request_meeting_access part.
            url = resource_url(self.context, self.request) + 'request_access'
            return HTTPFound(location = url)

        self.response['get_polls'] = self._get_polls
        
        colkwargs = dict(group_name = 'meeting_widgets',
                         col_one = self.context.get_field_value('meeting_left_widget', 'description_richtext'),
                         col_two = self.context.get_field_value('meeting_right_widget', None),
                         )
        self.response['meeting_columns'] = self.api.render_single_view_component(self.context, self.request,
                                                                                 'main', 'columns',
                                                                                 **colkwargs)
        return self.response

    def _get_polls(self, agenda_item):
        return agenda_item.get_content(iface=IPoll, states=('upcoming', 'ongoing', 'closed'), sort_on='sort_index')
        
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

    @view_config(name="ticket", context=IMeeting, renderer="templates/base_edit.pt", permission = NO_PERMISSION_REQUIRED)
    def claim_ticket(self):
        """ Handle claim of a ticket. It acts in two ways:
            - The normal way is that a user is authenticated and clicks the link in
              the email sent by the ticket invite system. That will be a GET-request,
              and the user in question will never see this form.
            - The other usecase is simly going to the link directly, or if for instance
              the link was cut off and the form didn't pass validation for the email + token.
              In that case, the form will be rendered so the user can cut and paste the token.
        """
        if not self.api.userid:
            msg = _('login_to_access_meeting_notice',
                    default=u"Welcome to VoteIT. To open the meeting you have been invited to please register in the form below. If you are already registered, please login.")
            self.api.flash_messages.add(msg, type='info')
            came_from = urllib.quote(self.request.url)
            url = "%slogin?came_from=%s" % (resource_url(self.api.root, self.request), came_from)
            return HTTPFound(location=url)

        self.response['title'] = _(u"Meeting Access")
        schema = createSchema('ClaimTicketSchema', validator = deferred_token_form_validator).bind(context=self.context, request=self.request)
        form = Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)

        if 'add' in self.request.POST or \
            'email' in self.request.GET and 'token' in self.request.GET:

            controls = self.request.params.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            ticket = self.context.invite_tickets[appstruct['email']]
            ticket.claim(self.request)
            self.api.flash_messages.add(_(u"You've been granted access to the meeting. Welcome!"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)
        
        if 'cancel' in self.request.POST:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.api.root, self.request)
            return HTTPFound(location=url)

        #No action - Render add form
        self.response['form'] = form.render()
        return self.response

    
    @view_config(name="add_tickets", context=IMeeting, renderer="templates/base_edit.pt", permission=security.MANAGE_GROUPS)
    def add_tickets(self):
        """ Add ticket invites to this meeting.
            Renders a form where you can paste email addresses and select which roles they
            should have once they register. When the form is submitted, it will also email
            users.
        """
        self.response['title'] = _(u"Send meeting invitations")

        post = self.request.POST
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        schema = createSchema('AddTicketsSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)

        form = Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)

        if 'add' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            emails = appstruct['emails'].splitlines()
            message = appstruct['message']
            roles = appstruct['roles']
            for email in emails:
                obj = createContent('InviteTicket', email, roles, message)
                self.context.add_invite_ticket(obj, self.request) #Will also email user
            
            msg = _('sent_tickets_text', default=u"Successfully added and sent ${mail_count} invites", mapping={'mail_count':len(emails)} )
            self.api.flash_messages.add(msg)

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render add form
        self.response['form'] = form.render()
        return self.response

    @view_config(name="manage_tickets", context=IMeeting, renderer="templates/base_edit.pt", permission=security.MANAGE_GROUPS)
    def manage_tickets(self):
        """ A form for handling and reviewing already sent tickets.
        """
        self.response['title'] = _(u"Current invitations")

        schema = createSchema('ManageTicketsSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)
            
        form = Form(schema, buttons=(button_resend, button_delete, button_cancel,))
        self.api.register_form_resources(form)

        post = self.request.POST

        emails = ()

        if 'resend' in post or 'delete' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
                if appstruct['apply_to_all'] == True:
                    emails = [x.email for x in self.context.invite_tickets.values() if x.get_workflow_state() != u'closed']
                else:
                    emails = appstruct['emails']
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response

        if emails and 'resend' in post:
            for email in emails:
                self.context.invite_tickets[email].send(self.request)
            
            self.api.flash_messages.add(_('resent_invites_notice',
                                          default=u"Resending ${count_emails} invites",
                                          mapping={'count_emails':len(emails)}))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if emails and 'delete' in post:
            for email in emails:
                del self.context.invite_tickets[email]
            
            self.api.flash_messages.add(_('deleting_invites_notice',
                                          default=u"Deleting ${count_emails} invites",
                                          mapping={'count_emails':len(emails)}))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)
        
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render add form
        self.response['form'] = form.render()
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
                 renderer = "templates/base_edit.pt", permission = NO_PERMISSION_REQUIRED)
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
            return HTTPFound(location=url)
        
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
            
        form = Form(schema, buttons=(button_save, button_cancel), use_ajax=True, ajax_options=ajax_options)
        self.api.register_form_resources(form)
        fanstaticlib.jquery_form.need()

        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                if self.request.is_xhr:
                    return Response(render("templates/ajax_edit.pt", self.response, request = self.request))
                
                return self.response
            
            self.context.set_field_appstruct(appstruct)
            
            url = resource_url(self.context, self.request)
            if self.request.is_xhr:
                return Response(headers = [('X-Relocate', url)])
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))

            url = resource_url(self.context, self.request)
            if self.request.is_xhr:
                return Response(headers = [('X-Relocate', url)])
            return HTTPFound(location=url)

        #No action - Render form
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = form.render(appstruct)
        return self.response
    
    @view_config(context=IMeeting, name="handle_agenda_items", renderer="templates/handle_agenda_items.pt", permission=security.EDIT)
    def handle_agenda_items(self):
        post = self.request.POST
        if 'cancel' in self.request.POST:
            url = self.request.resource_url(self.context, 'handle_agenda_items')
            return HTTPFound(location = url)

        if 'change' in post:
            state_id = self.request.POST['state_id']
            controls = self.request.POST.items()
            for (k, v) in controls:
                if k == 'ais':
                    ai = self.context[v]
                    try:
                        ai.set_workflow_state(self.request, state_id)
                    except WorkflowError, e:
                        self.api.flash_messages.add(_('Unable to change state on ${title}, ${error}', mapping={'title': ai.title}), type='error')
            self.api.flash_messages.add(_('States updated'))

        state_info = _dummy_agenda_item.workflow.state_info(None, self.request)
        def _translated_state_title(state):
            for info in state_info:
                if info['name'] == state:
                    return self.api.tstring(info['title'])
        
            return state
        self.response['translated_state_title'] = _translated_state_title
    
        self.response['find_resource'] = find_resource
        self.response['states'] = states = ('ongoing', 'upcoming', 'closed', 'private') 
        self.response['ais'] = {}
        for state in states:
            context_path = resource_path(self.context)
            query = dict(
                path = context_path,
                content_type = 'AgendaItem',
                sort_index = 'order',
                workflow_state = state,
            )
            self.response['ais'][state] = self.api.get_metadata_for_query(**query)
        self.response['came_from'] = self.request.url
        
        fanstaticlib.jquery_deform.need()

        return self.response
    
    @view_config(context=IMeeting, name="order_agenda_items", renderer="templates/order_agenda_items.pt", permission=security.EDIT)
    def order_agenda_items(self):
        self.response['title'] = _(u"order_agenda_items_view_title",
                                   default = u"Drag and drop agenda items to reorder")

        post = self.request.POST
        if 'cancel' in self.request.POST:
            url = resource_url(self.context, self.request)
            return HTTPFound(location = url)

        if 'save' in post:
            controls = self.request.POST.items()
            ais = []
            order = 0
            for (k, v) in controls:
                if k == 'agenda_items':
                    ai = self.context[v]
                    ai.set_field_appstruct({'order': order})
                    order += 1
            self.api.flash_messages.add(_('Order updated'))
            
        context_path = resource_path(self.context)
        query = dict(
            path = context_path,
            content_type = 'AgendaItem',
            sort_index = 'order',
        )
        self.response['brains'] = self.api.get_metadata_for_query(**query)
        
        fanstaticlib.jquery_deform.need()

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

_dummy_agenda_item = AgendaItem()