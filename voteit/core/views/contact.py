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


button_send = deform.Button('send', title = _("Send"), css_class = 'btn btn-primary')


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
