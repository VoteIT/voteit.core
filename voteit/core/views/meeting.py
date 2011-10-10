import urllib

from deform import Form
from deform.exception import ValidationFailure
from pyramid.renderers import get_renderer
from pyramid.security import has_permission
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.url import resource_url
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_resend
from voteit.core.models.schemas import button_delete
from voteit.core.validators import deferred_token_form_validator


class MeetingView(BaseView):
    
    @view_config(context=IMeeting, renderer="templates/meeting.pt")
    def meeting_view(self):
        """ Meeting view behaves a bit differently than regular views since
            it should allow users to request access if unauthorized is raised.
        """
        if not has_permission(security.VIEW, self.context, self.request):
            self.api.flash_messages.add(_(u"You're not allowed access to this meeting."), type='error')
            
            url = self.api.resource_url(self.api.root, self.request)
            return HTTPFound(location = url)
        
        self.response['check_section_closed'] = self._is_section_closed
        self.response['section_overview_macro'] = self.section_overview_macro
        
        states = ('ongoing', 'upcoming', 'closed')
        over_limit = {}
        agenda_items = {}
        for state in states:
            if 'log_'+state in self.request.GET and self.request.GET['log_'+state] == 'all':
                limit = 0
            else:
                limit = 5
            ais = self.context.get_content(iface=IAgendaItem, states=state, sort_on='start_time')
            if limit and len(ais) > limit:
                #Over limit
                over_limit[state] = len(ais) - limit
                agenda_items[state] = ais[-limit:] #Only the 5 last entries
            else:
                #Not over limit
                over_limit[state] = 0
                agenda_items[state] = ais
        
        self.response['agenda_items'] = agenda_items
        self.response['over_limit'] = over_limit
        self.response['get_polls'] = self._get_polls
        
        return self.response

    def _get_polls(self, agenda_item):
        return agenda_item.get_content(iface=IPoll, states=('upcoming', 'ongoing', 'closed'), sort_on='start_time')

    @property
    def section_overview_macro(self):
        return get_renderer('templates/macros/meeting_overview_section.pt').implementation().macros['main']

    def _is_section_closed(self, section):
        return self.request.cookies.get(section, None)

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

        self.response['participants'] = tuple(sorted(results, key = _sorter))
        self.response['context_effective_principals'] = security.context_effective_principals
        return self.response

    @view_config(name="meeting_access", context=IMeeting, renderer="templates/meeting_access.pt", permission=security.VIEW)
    def meeting_access(self):
        self.response['security_appstruct'] = self.context.get_security_appstruct()['userids_and_groups']
        self.response['form'] = True
        self.response['moderator'] = security.ROLE_MODERATOR
        self.response['participant'] = security.ROLE_PARTICIPANT
        self.response['voter'] = security.ROLE_VOTER
        self.response['viewer'] = security.ROLE_VIEWER
        return self.response

    @view_config(name="ticket", context=IMeeting, renderer="templates/base_edit.pt")
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
        schema = createSchema('AddTicketsSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)

        form = Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)

        post = self.request.POST
        if 'add' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            emails = appstruct['emails'].splitlines()
            message = appstruct['message']
            for email in emails:
                obj = createContent('InviteTicket', email, appstruct['roles'], message)
                self.context.add_invite_ticket(obj, self.request) #Will also email user
            
            msg = _('sent_tickets_text', default=u"Successfully added and sent ${mail_count} invites", mapping={'mail_count':len(emails)} )
            self.api.flash_messages.add(msg)

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))

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
        
    @view_config(name="navigation_section", context=IMeeting, renderer="templates/navigation_section.pt", permission=security.VIEW)
    def navigation_section(self):
        section = self.request.GET.get('section', None)
        agenda_items = ()
        if not self.request.cookies.get("%s-%s" % (self.context.uid, section)):
            if section:
                agenda_items = self.api.get_restricted_content(self.context, content_type='AgendaItem', states=section)
            
        self.response['agenda_items'] = agenda_items 
        return self.response
