from arche.utils import get_content_schemas
from arche.views.base import BaseForm
from arche.views.base import BaseView
from arche.views.base import button_add
from arche.views.base import button_cancel
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.view import view_defaults
import deform

from voteit.core import _
from voteit.core import security
from voteit.core.fanstaticlib import voteit_manage_tickets_js
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.invite_ticket import claim_ticket
from voteit.core.models.invite_ticket import send_invite_ticket
from voteit.core.models.invite_ticket import claim_and_send_notification


@view_defaults(context = IMeeting)
class TicketView(BaseView):
    """ View for all things that have to do with meeting invitation tickets. """

    @view_config(name = 'ticket_login', renderer = "voteit.core:templates/ticket_login.pt", permission = NO_PERMISSION_REQUIRED)
    def ticket_login(self):
        """ If user is not logged in, display login information.
        """
        return {}

    @view_config(name = 'ticket_claim', renderer = "voteit.core:templates/ticket_claim.pt", permission = NO_PERMISSION_REQUIRED)
    def ticket_claim(self):
        """ After login or registration, redirect back here, where information about the ticket will be displayed,
            and a confirmation that you want to use the ticket for the current user.
            
            While we use a regular deform form, it's not ment to be displayed or handle any validation.
        """
        if not self.request.authenticated_userid:
            raise HTTPForbidden("Direct access to this view for unauthorized users not allowed.")
        schema = get_content_schemas(self.request.registry)['Meeting']['claim_ticket']()
        schema = schema.bind(context = self.context, request = self.request, view = self)
        form = deform.Form(schema, buttons = (button_add, button_cancel,))
        if self.request.GET.get('claim'):
            controls = self.request.params.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                msg = _(u"ticket_validation_fail",
                        default = u"Ticket validation failed. Either the ticket doesn't exist, was already used or the url used improperly. "
                                  u"If you need help, please contact the moderator that invited you to this meeting.")
                self.flash_messages.add(msg, type = 'danger', auto_destruct = False)
                url = self.request.resource_url(self.root)
                return HTTPFound(location = url)
            #Everything in order, claim ticket
            ticket = self.context.invite_tickets[appstruct['email']]
            claim_ticket(ticket, self.request, self.request.authenticated_userid)
            self.flash_messages.add(_(u"You've been granted access to the meeting. Welcome!"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        #No action, render page
        claim_action_query = dict(
            claim = '1',
            email = self.request.GET.get('email', ''),
            token = self.request.GET.get('token', ''),
        )
        #FIXME: Use logout button + redirect link to go back to claim ticket
        return {'claim_action_url': self.request.resource_url(self.context, 'ticket_claim', query = claim_action_query)}

    @view_config(name = "ticket", permission = NO_PERMISSION_REQUIRED)
    def ticket_redirect(self):
        """ Handle incoming ticket url.
            Either redirect to information about registration, or the page about using the ticket.
            
            Note: Don't validate ticket until user has logged in. At least that makes bruteforcing it a bit harder.
        """
        email = self.request.GET.get('email', '')
        token = self.request.GET.get('token', '')
        #Authenticated users
        if self.request.authenticated_userid:
            if email and token:
                url = self.request.resource_url(self.context, 'ticket_claim', query = {'email': email, 'token': token})
            else:
                url = self.request.resource_url(self.context)
                msg = _(u"ticket_link_wrong_parameters_error",
                        default = U"The ticket link did not contain a token and an email address. Perhaps you came to this page by mistake?")
                self.flash_messages.add(msg, type = 'danger')
        #Unauthenticated users
        else:
            self.flash_messages.add(_("You need to login or register to use an inivitation ticket."))
            url = self.request.resource_url(self.root, 'login')
        return HTTPFound(location = url)

    @view_config(name = "manage_tickets", renderer = "voteit.core:templates/manage_tickets.pt", permission = security.MANAGE_GROUPS)
    def manage_tickets(self):
        """ Handle and review tickets. """
        if self.request.method == 'POST':
            data = self.request.POST.dict_of_lists()
            if 'email' not in data:
                self.flash_messages.add(_("Nothing selected - nothing to do!"), type = "danger")
                return HTTPFound(location = self.request.url)
            if 'remove' in data:
                for email in data['email']:
                    del self.context.invite_tickets[email]
                self.flash_messages.add(_("Removed ${count} tickets", mapping = {'count': len(data['email'])}))
                return HTTPFound(location = self.request.url)
            if 'resend' in data:
                total = len(data['email'])
                if total > 1:
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
                            send_invite_ticket(ticket, self.request, data['message'][0])
                            resent += 1
                        else:
                            aborted += 1
                    if not aborted:
                        msg = _(u"Resent ${count} successfully",
                                mapping = {'count': resent})
                    else:
                        msg = _(u"Resent ${count} of ${total}. ${aborted} were not sent since they're already claimed",
                                mapping = {'count': resent, 'total': total, 'aborted': aborted})
                    self.flash_messages.add(msg)
                    return HTTPFound(location = self.request.url)
        voteit_manage_tickets_js.need()
        #self.response['tabs'] = self.api.render_single_view_component(self.context, self.request, 'tabs', 'manage_tickets')
        closed = 0
        results = []
        never_invited = []
        for ticket in self.context.invite_tickets.values():
            results.append(ticket)
            if ticket.closed != None:
                closed += 1
            if len(ticket.sent_dates) == 0:
                never_invited.append(ticket.email)
        response = {}
        response['invite_tickets'] = results
        response['closed_count'] = closed
        response['never_invited'] = never_invited
        response['roles_dict'] = dict(security.MEETING_ROLES)
        return response

    @view_config(name = "send_tickets", renderer = "voteit.core:templates/send_tickets.pt", permission = security.MANAGE_GROUPS)
    def send_tickets(self):
        return {'emails': self.request.session.get('send_tickets.emails', ())}

    @view_config(name = "send_tickets", renderer = "json", permission = security.MANAGE_GROUPS, xhr = True)
    def send_tickets_action():
        session = self.request.session
        emails = session['send_tickets.emails'][:20]
        message = session['send_tickets.message']
        _marker = object()
        for email in emails:
            ticket = self.context.invite_tickets[email]
            #Check if email exists and is validated
            #If it does exist, use the ticket and then notify the user instead
            user = self.root['users'].get_user_by_email(email, default = _marker, only_validated = True)
            if user != _marker:
                claim_and_send_notification(ticket, self.request, message = message)
            else:
                send_invite_ticket(ticket, self.request, message = message)
            session['send_tickets.emails'].remove(email)
        if len(session['send_tickets.emails']) == 0:
            del session['send_tickets.emails']
            del session['send_tickets.message']
        return {'sent': len(emails), 'remaining': len(session.get('send_tickets.emails', ()))}


@view_config(name = "add_tickets",
             context = IMeeting,
             renderer = "arche:templates/form.pt",
             permission = security.MANAGE_GROUPS)
class AddTicketsForm(BaseForm):
    schema_name = 'add_tickets'
    type_name = 'Meeting'
    #self.response['tabs'] = self.api.render_single_view_component(self.context, self.request, 'tabs', 'manage_tickets')

    title = _("Invite participants")

    @property
    def buttons(self):
        return (self.button_add, self.button_cancel)

    def add_success(self, appstruct):
        emails = appstruct['emails'].splitlines()
        roles = appstruct['roles']
        added = 0
        rejected = 0
        for email in emails:
            result = self.context.add_invite_ticket(email, roles, sent_by = self.request.authenticated_userid)
            if result:
                added += 1
            else:
                rejected += 1
        if not rejected:
            msg = _('added_tickets_text', default = "Successfully added ${added} invites",
                    mapping={'added': added})
        elif not added:
            msg = _('no_tickets_added',
                    default = "No tickets added - all you specified probably exist already. (Proccessed ${rejected})",
                    mapping = {'rejected': rejected})
            self.flash_messages.add(msg, type = 'warning', auto_destruct = False)
            url = self.request.resource_url(self.context, 'add_tickets')
            return HTTPFound(location = url)
        else:
            msg = _('added_tickets_text_some_rejected',
                    default=u"Successfully added ${added} invites but discarded ${rejected} since they already existed or were already used.",
                    mapping={'added': added, 'rejected': rejected})
        self.flash_messages.add(msg)
        self.request.session['send_tickets.emails'] = emails
        self.request.session['send_tickets.message'] = appstruct['message']
        url = self.request.resource_url(self.context, 'send_tickets')
        return HTTPFound(location = url)
