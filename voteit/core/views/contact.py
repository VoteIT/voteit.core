from deform import Form
from deform.exception import ValidationFailure
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_edit import BaseEdit
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.schemas import button_send
from voteit.core.security import find_authorized_userids
from voteit.core.security import MODERATE_MEETING


class ContactView(BaseEdit):
    """ Contact and support view. """

    @view_config(name = 'contact', context=IMeeting, renderer="templates/base_edit.pt", permission=security.VIEW)
    def contact(self):
        """ Contact moderators of the meeting
        """
        schema = createSchema('ContactSchema').bind(context = self.context, request = self.request, api = self.api)
        form = Form(schema, action=self.request.resource_url(self.context, 'contact'), buttons=(button_send,))
        self.api.register_form_resources(form)

        post = self.request.POST
        if self.request.method == 'POST':
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            meeting = self.context
            
            if appstruct.get('email', None):
                sender = appstruct['email']
                if self.api.user_profile:
                    sender += " <%s>" % self.api.user_profile.title
            else:
                sender = "%s <%s>" % (meeting.get_field_value('meeting_mail_name'), meeting.get_field_value('meeting_mail_address'))

            recipients = []
            for userid in find_authorized_userids(meeting, (MODERATE_MEETING,)):
                user = self.api.get_user(userid)
                email = user.get_field_value('email')
                if email:
                    recipients.append(email)

            response = {
                        'api': self.api,
                        'meeting': meeting,
                        'name': appstruct['name'],
                        'email': appstruct['email'],
                        'subject': appstruct['subject'],
                        'message': appstruct['message'],
                        }
            body_html = render('templates/email/help_contact.pt', response, request=self.request)
            
            msg = Message(subject=self.api.translate(_(u"VoteIT - ${meeting}", mapping={"meeting": meeting.get_field_value('title')})),
                          sender = sender and sender or None,
                          recipients=recipients,
                          html=body_html)
            mailer = get_mailer(self.request)
            mailer.send(msg)
            self.api.flash_messages.add(_(u"Message sent to the moderators"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location = url)
            
        #No action - Render form
        self.response['form'] = form.render()
        return self.response


    @view_config(name = 'support', context=ISiteRoot, renderer="voteit.core.views:templates/base_edit.pt", permission=NO_PERMISSION_REQUIRED)
    @view_config(name = 'support', context=IMeeting, renderer="voteit.core.views:templates/base_edit.pt", permission=security.VIEW)
    def support(self):
        """ Support form - requires support email to be set!
        """
        support_email = self.api.root.get_field_value('support_email', None)
        if not support_email:
            self.api.flash_messages.add(_(u"No support email set for this site. Form won't work!"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location = url)
        schema = createSchema('SupportSchema').bind(context = self.context, request = self.request, api = self.api)
        form = Form(schema, action=self.request.resource_url(self.context, 'support'), buttons=(button_send,))
        self.api.register_form_resources(form)

        post = self.request.POST
        if self.request.method == 'POST':
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            sender = appstruct['email'] and appstruct['email'] or "VoteIT <noreply@voteit.se>"
            response = {'api': self.api,
                        'meeting': self.api.meeting,
                        'name': appstruct['name'],
                        'email': appstruct['email'],
                        'subject': appstruct['subject'],
                        'message': appstruct['message'],
                        'meeting_title': appstruct.get('meeting_title', ''),
                        }
            body_html = render('templates/email/support.pt', response, request = self.request)
            subject = "[%s] | %s" % (self.api.translate(_(u"VoteIT Support")), appstruct['subject'])
            msg = Message(subject = subject,
                          sender = sender and sender or None,
                          recipients=(support_email,),
                          html=body_html)
            mailer = get_mailer(self.request)
            mailer.send(msg)
            self.api.flash_messages.add(_(u"Support request sent!"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location = url)

        #No action - Render form
        self.response['form'] = form.render()
        return self.response
