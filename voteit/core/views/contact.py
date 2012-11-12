from deform import Form
from deform.exception import ValidationFailure
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.httpexceptions import HTTPFound
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_edit import BaseEdit
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_send
from voteit.core import fanstaticlib
from voteit.core.security import find_authorized_userids
from voteit.core.security import MODERATE_MEETING


class ContactView(BaseEdit):
    """ Contact view - refactor this into separate functions. """

    @view_config(name = 'contact', context=IMeeting, renderer="templates/base_edit.pt", permission=security.VIEW)
    def contact(self):
        """ Contact moderators of the meeting
        """
        fanstaticlib.jquery_form.need()
        
        schema = createSchema('ContactSchema').bind(context = self.context, request = self.request, api = self.api)
        add_csrf_token(self.context, self.request, schema)
            
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
