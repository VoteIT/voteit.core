from urllib import quote

import deform
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.url import resource_url
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_resend
from voteit.core.models.schemas import button_delete
from voteit.core.validators import deferred_token_form_validator


class TicketView(BaseView):
    """ View for all things that have to do with meeting invitation tickets. """


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
            came_from = quote(self.request.url)
            url = "%slogin?came_from=%s" % (resource_url(self.api.root, self.request), came_from)
            return HTTPFound(location=url)

        self.response['title'] = _(u"Meeting Access")
        schema = createSchema('ClaimTicketSchema', validator = deferred_token_form_validator).bind(context=self.context, request=self.request)
        form = deform.Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)

        if 'add' in self.request.POST or \
            'email' in self.request.GET and 'token' in self.request.GET:

            controls = self.request.params.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
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

        form = deform.Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)

        if 'add' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
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
            
        form = deform.Form(schema, buttons=(button_resend, button_delete, button_cancel,))
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
            except deform.ValidationFailure, e:
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
