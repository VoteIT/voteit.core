from __future__ import unicode_literals
 
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.renderers import render
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from arche.utils import send_email
from arche.views.base import BaseForm
import deform

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.security import MODERATE_MEETING
from voteit.core.security import ROLE_MODERATOR
from voteit.core.security import find_authorized_userids
from voteit.core.security import find_role_userids



button_send = deform.Button('send', title = _("Send"), css_class = 'btn btn-primary')


@view_config(name = 'contact',
             context = IMeeting,
             renderer = "arche:templates/form.pt",
             permission = security.VIEW)
class ContactView(BaseForm):
    """ Contact and support form. """
    schema_name = "contact"
    type_name = "Meeting"

    @property
    def buttons(self):
        return (button_send, self.button_cancel)

    def get_recipients(self):
        recipients = []
        for userid in find_role_userids(self.context, ROLE_MODERATOR):
            user = self.root.users.get(userid, None)
            if user and user.email:
                recipients.append(user.email)
        if not recipients:
            for userid in find_authorized_userids(self.context, (MODERATE_MEETING,)):
                user = self.root.users.get(userid, None)
                if user and user.email:
                    recipients.append(user.email)
        return recipients

    def send_success(self, appstruct):
        if appstruct.get('email', None):
            sender = appstruct['email']
            if self.request.profile:
                sender += " <%s>" % self.request.profile.title
        else:
            sender = None
        response = {'meeting': self.request.meeting,
                    'name': appstruct['name'],
                    'email': appstruct['email'],
                    'subject': appstruct['subject'],
                    'message': appstruct['message'],
                    'meeting_title': appstruct.get('meeting_title', ''),}
        
        body_html = render('voteit.core:templates/email/help_contact.pt', response, request = self.request)
        subject = "[%s] %s" % (self.context.title, appstruct['subject'])
        recipients = self.get_recipients()
        send_email(self.request, subject, recipients, body_html, sender = sender, send_immediately = True)
        self.flash_messages.add(_("Message sent to the moderators"))
        url = self.request.resource_url(self.context)
        return HTTPFound(location = url)


@view_config(name = 'support',
             context = ISiteRoot,
             renderer = "arche:templates/form.pt",
             permission = NO_PERMISSION_REQUIRED)
@view_config(name = 'support',
             context = IMeeting,
             renderer = "arche:templates/form.pt",
             permission = security.VIEW)
class SupportForm(BaseForm):
    schema_name = "support"

    @property
    def type_name(self):
        return self.context.type_name

    @property
    def buttons(self):
        return (button_send, self.button_cancel)

    def __call__(self):
        if not self.request.root.support_email:
            raise HTTPForbidden(_(u"No support email set for this site. Form won't work!"))
        return super(SupportForm, self).__call__()

    def send_success(self, appstruct):
        sender = appstruct['email'] and appstruct['email'] or None
        response = {'meeting': self.request.meeting,
                    'name': appstruct['name'],
                    'email': appstruct['email'],
                    'subject': appstruct['subject'],
                    'message': appstruct['message'],
                    'meeting_title': appstruct.get('meeting_title', ''),}
        body_html = render('voteit.core:templates/email/support.pt', response, request = self.request)
        title = "%s %s" % (self.root.head_title, self.request.localizer.translate(_("Support")))
        subject = "[%s] | %s" % (title, appstruct['subject'])
        send_email(self.request, subject, [self.root.support_email], body_html, sender = sender, send_immediately = True)
        self.flash_messages.add(_("Message sent"))
        return HTTPFound(location = self.request.resource_url(self.context))
