import urllib
import json

import colander
from deform import Form
from deform.exception import ValidationFailure
from pyramid.security import has_permission
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPRedirection
from pyramid.url import resource_url
from pyramid.traversal import resource_path
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_save
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_resend
from voteit.core.models.schemas import button_delete
from voteit.core.validators import deferred_token_form_validator
from betahaus.viewcomponent.interfaces import IViewGroup
from voteit.core.helpers import generate_slug


class MeetingView(BaseView):
    
    @view_config(context=IMeeting, renderer="templates/meeting.pt", permission = NO_PERMISSION_REQUIRED)
    def meeting_view(self):
        """ Meeting view behaves a bit differently than regular views since
            it should allow users to request access if unauthorized is raised.
        """
        if not has_permission(security.VIEW, self.context, self.request):
            if self.api.userid:
                #We delegate permission checks to the request_meeting_access part.
                url = resource_url(self.context, self.request) + '@@request_access'
                return HTTPFound(location = url)
            else:
                msg = _(u"You're not logged in - before you can access meetings you need to do that.")
            self.api.flash_messages.add(msg, type='error')
            url = self.api.resource_url(self.api.root, self.request)
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

    @view_config(name="participants", context=IMeeting, renderer="templates/participants.pt", permission=security.VIEW)
    def participants_view(self):
        """ List all participants in this meeting, and their permissions. """
        users = self.api.root.users
        
        results = []
        for userid in security.find_authorized_userids(self.context, (security.VIEW,)):
            user = users.get(userid, None)
            if user:
                results.append(user)
        
        def _sorter(obj):
            return obj.get_field_value('first_name')

        #Viewer role isn't needed, since only users who can view will be listed here.
        self.response['role_moderator'] = security.ROLE_MODERATOR
        self.response['role_discuss'] = security.ROLE_DISCUSS
        self.response['role_propose'] = security.ROLE_PROPOSE
        self.response['role_voter'] = security.ROLE_VOTER
        self.response['participants'] = tuple(sorted(results, key = _sorter))
        self.response['context_effective_principals'] = security.context_effective_principals
        return self.response
        
    @view_config(name="participants_emails", context=IMeeting, renderer="templates/participants_emails.pt", permission=security.MANAGE_GROUPS)
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
            url = "%s@@login?came_from=%s" % (resource_url(self.api.root, self.request), came_from)
            return HTTPFound(location=url)

        schema = createSchema('ClaimTicketSchema', validator = deferred_token_form_validator).bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)

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
        msg = _(u"Meeting Access")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render()
        return self.response

    
    @view_config(name="add_tickets", context=IMeeting, renderer="templates/base_edit.pt", permission=security.MANAGE_GROUPS)
    def add_tickets(self):
        """ Add ticket invites to this meeting.
            Renders a form where you can paste email addresses and select which roles they
            should have once they register. When the form is submitted, it will also email
            users.
        """
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
        msg = _(u"Send meeting invitations")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render()
        return self.response

    @view_config(name="manage_tickets", context=IMeeting, renderer="templates/base_edit.pt", permission=security.MANAGE_GROUPS)
    def manage_tickets(self):
        """ A form for handling and reviewing already sent tickets.
        """
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
        msg = _(u"Current invitations")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render()
        return self.response

    @view_config(name="manage_layout", context=IMeeting, renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def manage_layout(self):
        """ Manage layout
        """
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
        msg = _(u"Layout")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render(appstruct)
        return self.response

    @view_config(name = 'request_access', context = IMeeting,
                 renderer = "templates/base_edit.pt", permission = NO_PERMISSION_REQUIRED)
    def request_meeting_access(self):
        view_group = self.request.registry.getUtility(IViewGroup, name = 'request_meeting_access')
        access_policy = self.context.get_field_value('access_policy', 'invite_only')
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
    @view_config(context=ISiteRoot, name="meeting_wizard_step1", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def presentation(self):

        schema = createSchema("PresentationMeetingSchema").bind(context=self.context, request=self.request)
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
            
            # In wizard mode data should not be saved to the meeting but to a session variable
            if ISiteRoot.providedBy(self.context):
                del appstruct['csrf_token']
                self.request.session['wizard'] = appstruct
                url = resource_url(self.context, self.request) + "@@meeting_wizard_step2"
            else:
                self.context.set_field_appstruct(appstruct)
                url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            # If in wizard mode delete the session if canceling
            if wizard:
                del self.request.session['wizard']
            
            self.api.flash_messages.add(_(u"Canceled"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render form
        if IMeeting.providedBy(self.context):
            appstruct = self.context.get_field_appstruct(schema)
        else:
            appstruct = {}
        msg = _(u"Presentation")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render(appstruct)
        return self.response

    
    @view_config(context=IMeeting, name="mail_settings", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    @view_config(context=ISiteRoot, name="meeting_wizard_step2", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def mail_settings(self):
        
        schema = createSchema("MailSettingsMeetingSchema").bind(context=self.context, request=self.request)
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
            
            # In wizard mode data should not be saved to the meeting but to a session variable
            if ISiteRoot.providedBy(self.context):
                del appstruct['csrf_token']
                wizard = self.request.session.get('wizard', None)
                if not wizard:
                    raise ValueError(_(u"Missing data from previous steps"))
                wizard = (appstruct.items() + dict(wizard).items())
                self.request.session['wizard'] = wizard
                url = resource_url(self.context, self.request) + "@@meeting_wizard_step3"
            else:
                self.context.set_field_appstruct(appstruct)
                url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            # If in wizard mode delete the session if canceling
            if wizard:
                del self.request.session['wizard']
            
            self.api.flash_messages.add(_(u"Canceled"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render form
        if IMeeting.providedBy(self.context):
            appstruct = self.context.get_field_appstruct(schema)
        else:
            appstruct = {}
        msg = _(u"Mail settings")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render(appstruct)
        return self.response
    
    @view_config(context=IMeeting, name="access_policy", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    @view_config(context=ISiteRoot, name="meeting_wizard_step3", renderer="templates/base_edit.pt", permission=security.MODERATE_MEETING)
    def access_policy(self):
        
        schema = createSchema("AccessPolicyMeetingSchema").bind(context=self.context, request=self.request)
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
            
            # In wizard mode a new meeting should be created
            if ISiteRoot.providedBy(self.context):
                del appstruct['csrf_token']
                wizard = self.request.session.get('wizard', None)
                if not wizard:
                    raise ValueError(_(u"Missing data from previous steps"))
                appstruct = (appstruct.items() + dict(wizard).items())
                
                kwargs = {}
                kwargs.update(appstruct)
                if self.api.userid:
                    kwargs['creators'] = [self.api.userid]
    
                obj = createContent('Meeting', **kwargs)
                name = generate_slug(self.context, obj.title, 50)
                self.context[name] = obj
                
                del self.request.session['wizard']
            else:
                self.context.set_field_appstruct(appstruct)
            
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            # If in wizard mode delete the session if canceling
            if wizard:
                del self.request.session['wizard']
                
            self.api.flash_messages.add(_(u"Canceled"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render form
        if IMeeting.providedBy(self.context):
            appstruct = self.context.get_field_appstruct(schema)
        else:
            appstruct = {}
        msg = _(u"Access policy")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render(appstruct)
        return self.response
    
    
    @view_config(context=IMeeting, name="order_agenda_items", renderer="templates/order_agenda_items.pt", permission=security.EDIT)
    def order_agenda_items(self):
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

        form = Form(colander.Schema())
        self.response['form_resources'] = form.get_widget_resources()
        self.response['dummy_form'] = form.render()
        return self.response