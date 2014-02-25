import deform
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_resend
from voteit.core.models.schemas import button_send
from voteit.core.models.schemas import button_delete
from voteit.core.validators import deferred_token_form_validator
from voteit.core.fanstaticlib import voteit_manage_tickets_js
from voteit.core.fanstaticlib import voteit_send_invitations


class TicketView(BaseView):
    """ View for all things that have to do with meeting invitation tickets. """

    @view_config(name = 'ticket_login', context = IMeeting, renderer = "templates/ticket_login.pt", permission = NO_PERMISSION_REQUIRED)
    def ticket_login(self):
        """ If user is not logged in, display a registration button and the normal
            login form on the left hand side.
        """
        self.response['title'] = _(u"Login or register to gain access")
        self.response['came_from'] = self.request.GET.get('came_from', '')
        return self.response

    @view_config(name = 'ticket_claim', context = IMeeting, renderer = "templates/ticket_claim.pt", permission = NO_PERMISSION_REQUIRED)
    def ticket_claim(self):
        """ After login or registration, redirect back here, where information about the ticket will be displayed,
            and a confirmation that you want to use the ticket for the current user.
            
            While we use a regular deform form, it's not ment to be displayed or handle any validation.
        """
        if not self.api.userid:
            raise HTTPForbidden("Direct access to this view for unauthorized users not allowed.")
        schema = createSchema('ClaimTicketSchema', validator = deferred_token_form_validator)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        form = deform.Form(schema, buttons=(button_add, button_cancel))
        if self.request.GET.get('claim'):
            controls = self.request.params.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                msg = _(u"ticket_validation_fail",
                        default = u"Ticket validation failed. Either the ticket doesn't exist, was already used or the url used improperly. "
                                  u"If you need help, please contact the moderator that invited you to this meeting.")
                self.api.flash_messages.add(msg, type = 'error')
                url = self.request.resource_url(self.api.root)
                return HTTPFound(location = url)
            #Everything in order, claim ticket
            ticket = self.context.invite_tickets[appstruct['email']]
            ticket.claim(self.request)
            self.api.flash_messages.add(_(u"You've been granted access to the meeting. Welcome!"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        #No action, render page
        claim_action_query = dict(
            claim = '1',
            email = self.request.GET.get('email', ''),
            token = self.request.GET.get('token', ''),
        )
        #FIXME: Use logout button + redirect link to go back to claim ticket
        self.response['claim_action_url'] = self.request.resource_url(self.context, 'ticket_claim', query = claim_action_query)
        return self.response

    @view_config(name="ticket", context=IMeeting, permission = NO_PERMISSION_REQUIRED)
    def ticket_redirect(self):
        """ Handle incoming ticket url.
            Either redirect to information about registration, or the page about using the ticket.
            
            Note: Don't validate ticket until user has logged in. At least that makes bruteforcing it a bit harder.
        """
        email = self.request.GET.get('email', '')
        token = self.request.GET.get('token', '')
        #Authenticated users
        if self.api.userid:
            if email and token:
                url = self.request.resource_url(self.context, 'ticket_claim', query = {'email': email, 'token': token})
            else:
                url = self.request.resource_url(self.context)
                msg = _(u"ticket_link_wrong_parameters_error",
                        default = U"The ticket link did not contain a token and an email address. Perhaps you came to this page by mistake?")
                self.api.flash_messages.add(msg, type = 'error')
        #Unauthenticated users
        else:
            url = self.request.resource_url(self.context, 'ticket_login', query = {'came_from': self.request.url})
        return HTTPFound(location = url)

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
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        schema = createSchema('AddTicketsSchema')
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        form = deform.Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)
        self.response['tabs'] = self.api.render_single_view_component(self.context, self.request, 'tabs', 'manage_tickets')
        if 'add' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            emails = appstruct['emails'].splitlines()
            roles = appstruct['roles']
            added = 0
            rejected = 0
            for email in emails:
                result = self.context.add_invite_ticket(email, roles, sent_by = self.api.userid)
                if result:
                    added += 1
                else:
                    rejected += 1
            if not rejected:
                msg = _('added_tickets_text', default=u"Successfully added ${added} invites",
                        mapping={'added': added})
            elif not added:
                msg = _('no_tickets_added',
                        default = u"No tickets added - all you specified probably exist already. (Proccessed ${rejected})",
                        mapping = {'rejected': rejected})
                self.api.flash_messages.add(msg)
                url = self.request.resource_url(self.context, 'add_tickets')
                return HTTPFound(location = url)
            else:
                msg = _('added_tickets_text_some_rejected',
                        default=u"Successfully added ${added} invites but discarded ${rejected} since they already existed or were already used.",
                        mapping={'added': added, 'rejected': rejected})
            self.api.flash_messages.add(msg)
            self.request.session['send_tickets.emails'] = emails
            self.request.session['send_tickets.message'] = appstruct['message']
            url = self.request.resource_url(self.context, 'send_tickets')
            return HTTPFound(location = url)
        #No action - Render add form
        self.response['form'] = form.render()
        return self.response

    @view_config(name="manage_tickets", context=IMeeting, renderer="templates/manage_tickets.pt", permission=security.MANAGE_GROUPS)
    def manage_tickets(self):
        """ Handle and review tickets. """
        if self.request.method == 'POST':
            data = self.request.POST.dict_of_lists()
            if 'email' not in data:
                self.api.flash_messages.add(_(u"Nothing selected - nothing to do!"), type = "error")
                return HTTPFound(location = self.request.url)
            if 'remove' in data:
                for email in data['email']:
                    del self.context.invite_tickets[email]
                self.api.flash_messages.add(_(u"Removed ${count} tickets",
                                              mapping = {'count': len(data['email'])}))
                return HTTPFound(location = self.request.url)
            if 'resend' in data:
                total = len(data['email'])
                if total > 50:
                    #bulk send
                    self.request.session['send_tickets.emails'] = data['email']
                    self.request.session['send_tickets.message'] = data['message'][0]
                    return HTTPFound(location = self.request.resource_url(self.context, 'send_tickets'))
                else:
                    resent = 0
                    aborted = 0
                    for email in data['email']:
                        ticket = self.context.invite_tickets[email]
                        if not ticket.closed:
                            ticket.send(self.request, data['message'][0])
                            resent += 1
                        else:
                            aborted += 1
                    if not aborted:
                        msg = _(u"Resent ${count} successfully",
                                mapping = {'count': resent})
                    else:
                        msg = _(u"Resent ${count} of ${total}. ${aborted} were not sent since they're already claimed",
                                mapping = {'count': resent, 'total': total, 'aborted': aborted})
                    self.api.flash_messages.add(msg)
                    return HTTPFound(location = self.request.url)
        voteit_manage_tickets_js.need()
        self.response['tabs'] = self.api.render_single_view_component(self.context, self.request, 'tabs', 'manage_tickets')
        closed = 0
        results = []
        never_invited = []
        for ticket in self.context.invite_tickets.values():
            results.append(ticket)
            if ticket.closed != None:
                closed += 1
            if len(ticket.sent_dates) == 0:
                never_invited.append(ticket.email)
        self.response['invite_tickets'] = results
        self.response['closed_count'] = closed
        self.response['never_invited'] = never_invited
        self.response['roles_dict'] = dict(security.MEETING_ROLES)
        return self.response

    @view_config(name = "send_tickets", context = IMeeting, renderer = "templates/send_tickets.pt", permission = security.MANAGE_GROUPS)
    def send_tickets(self):
        emails = self.request.session.get('send_tickets.emails', ())
        if emails:
            voteit_send_invitations.need()
        self.response['emails'] = emails
        return self.response


@view_config(name = "send_tickets", context = IMeeting, renderer = "json", permission = security.MANAGE_GROUPS, xhr = True)
def send_tickets_action(context, request):
    session = request.session
    emails = session['send_tickets.emails'][:20]
    message = session['send_tickets.message']
    for email in emails:
        context.invite_tickets[email].send(request, message)
        session['send_tickets.emails'].remove(email)
    if len(session['send_tickets.emails']) == 0:
        del session['send_tickets.emails']
        del session['send_tickets.message']
    return {'sent': len(emails), 'remaining': len(session.get('send_tickets.emails', ()))}
