from pyramid.security import has_permission
from pyramid.view import view_config
from webob.exc import HTTPFound
import deform
import urllib
from deform.exception import ValidationFailure
from pyramid.exceptions import Forbidden
from pyramid.url import resource_url

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token


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
            
            #FIXME:
            #If user is authenticated:
#            if has_permission(security.REQUEST_MEETING_ACCESS, self.context, self.request):
#                url = self.api.resource_url(self.context, self.request) + 'request_meeting_access'
#                return HTTPFound(location = url)
            
            #Otherwise raise unauthorized
            #raise Forbidden("You can't request access to this meeting. Maybe you need to login, or it isn't allowed.")
        
        if self.context.get_workflow_state() == 'private':
            msg = _(u"This meeting is in the state <b>Private</b>. "
                    u"No regular meeting participants can see this meeting yet, and you won't be able to send invitations. "
                    u"If you want others to see it, you can set the meeting in the <b>Inactive</b> state by using the <b>set state</b> menu.")
            self.api.flash_messages.add(msg)
        
        self.response['get_state_ais'] = self._get_state_ais
        
        return self.response

    def _get_state_ais(self, state):
        return self.context.get_content(iface=IAgendaItem, state=state, sort_on='agenda_item_id')

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
                    default=u"To gain access to a meeting you need to use an access ticket that should have been mailed to you. If you've aldready registered, please login.")
            self.api.flash_messages.add(msg, type='error')

            came_from = urllib.quote(self.request.url)
            url = "%s@@login?came_from=%s" % (resource_url(self.api.root, self.request), came_from)
            return HTTPFound(location=url)
        
        ci = self.api.content_info['InviteTicket']
        schema = ci.schema(context=self.context, request=self.request, type='claim')
        add_csrf_token(self.context, self.request, schema)

        self.form = deform.Form(schema, buttons=('add', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        if 'add' in self.request.POST or \
            'email' in self.request.GET and 'token' in self.request.GET:

            controls = self.request.params.items()
            try:
                appstruct = self.form.validate(controls)
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
        self.response['form'] = self.form.render()
        return self.response

    
    @view_config(name="add_tickets", context=IMeeting, renderer="templates/base_edit.pt", permission=security.MANAGE_GROUPS)
    def add_tickets(self):
        """ Add ticket invites to this meeting.
            Renders a form where you can paste email addresses and select which roles they
            should have once they register. When the form is submitted, it will also email
            users.
        """
        ci = self.api.content_info['InviteTicket']
        schema = ci.schema(context=self.context, request=self.request, type='add')
        add_csrf_token(self.context, self.request, schema)

        self.form = deform.Form(schema, buttons=('add', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'add' in post:
            controls = post.items()
            try:
                appstruct = self.form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            emails = appstruct['emails'].splitlines()
            message = appstruct['message']
            for email in emails:
                obj = ci.type_class(email, appstruct['roles'], message)
                self.context.add_invite_ticket(obj, self.request) #Will also email user
            
            msg = _('sent_tickets_text', default=u"Successfully added and sent %(mail_count)s invites", mapping={'mail_count':len(emails)} )
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
        self.response['form'] = self.form.render()
        return self.response


    @view_config(name="manage_tickets", context=IMeeting, renderer="templates/base_view.pt", permission=security.MANAGE_GROUPS)
    def manage_tickets(self):
        """ A form for handling and reviewing already sent tickets.
        """
        ci = self.api.content_info['InviteTicket']
        schema = ci.schema(context=self.context, request=self.request, type='manage')
        add_csrf_token(self.context, self.request, schema)
            
        self.form = deform.Form(schema, buttons=('resend', 'delete', 'cancel',))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        def process_form():
            controls = post.items()
            try:
                appstruct = self.form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response

            return appstruct['emails']    

        if 'resend' in post:
            emails = process_form()
            for email in emails:
                self.context.invite_tickets[email].send(self.request)
            
            self.api.flash_messages.add(_(u"Resending %s invites" % len(emails)))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)            

        if 'delete' in post:
            emails = process_form()
            for email in emails:
                del self.context.invite_tickets[email]
            
            self.api.flash_messages.add(_(u"Deleting %s invites" % len(emails)))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)
        
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render add form
        msg = _(u"Current invitations")
        self.api.flash_messages.add(msg, close_button=False)

        self.response['form'] = self.form.render()
        return self.response

    @view_config(name="protocol", context=IMeeting, renderer="templates/protocol.pt", permission=security.VIEW)
    def protocol(self):
        self.response['log'] = self.api.logs.retrieve_entries(self.context.uid)
        
        return self.response
