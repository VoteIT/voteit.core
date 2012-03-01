from deform import Form
from deform.exception import ValidationFailure
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPRedirection
from pyramid.url import resource_url
from pyramid.renderers import render
from pyramid.response import Response
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_send
from voteit.core import fanstaticlib
from voteit.core.security import find_authorized_userids
from voteit.core.security import MODERATE_MEETING

class HelpView(BaseView):
    @view_config(name = 'contact', context=IMeeting, renderer="templates/ajax_edit.pt", permission=security.VIEW)
    def contact(self):
        """ Contact moderators of the meeting
        """
        fanstaticlib.jquery_form.need()
        
        schema = createSchema('ContactSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)
            
        form = Form(schema, action=resource_url(self.context, self.request)+"@@contact", buttons=(button_send,), formid="help-tab-contact-form", use_ajax=True)
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
            
            msg = Message(subject=_(u"VoteIT - ${meeting}", mapping={"meeting": meeting.get_field_value('title')}),
                          sender = sender and sender or None,
                          recipients=recipients,
                          html=body_html)
        
            mailer = get_mailer(self.request)
            mailer.send(msg)
            
            self.response['message'] = _(u"Message sent to the moderators")
            return Response(render("templates/ajax_success.pt", self.response, request = self.request))
            
        #No action - Render form
        appstruct = {}
        user = self.api.get_user(self.api.userid)
        if user:
            appstruct['name'] = user.title
            appstruct['email'] = user.get_field_value('email')
        self.response['form'] = form.render(appstruct=appstruct)
        return self.response
