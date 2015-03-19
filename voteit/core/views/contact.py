# from __future__ import unicode_literals
# 
# from betahaus.pyracont.factories import createSchema
# from pyramid.httpexceptions import HTTPFound
# from pyramid.httpexceptions import HTTPForbidden
# from pyramid.renderers import render
# from pyramid.security import NO_PERMISSION_REQUIRED
# from pyramid.view import view_config
# 
# from voteit.core import VoteITMF as _
# from voteit.core import security
# from voteit.core.helpers import send_email
# from voteit.core.models.interfaces import IMeeting
# from voteit.core.models.interfaces import ISiteRoot
# from voteit.core.models.schemas import button_cancel
# from voteit.core.models.schemas import button_send
# from voteit.core.security import MODERATE_MEETING
# from voteit.core.security import ROLE_MODERATOR
# from voteit.core.security import find_authorized_userids
# from voteit.core.security import find_role_userids
# from voteit.core.views.base_edit import BaseForm
# 


# FIXME: REFACTOR THIS
# 
# @view_config(name = 'contact',
#              context = IMeeting,
#              renderer = "voteit.core:views/templates/base_edit.pt",
#              permission = security.VIEW)
# class ContactView(BaseForm):
#     """ Contact and support view. """
#     buttons = (button_send, button_cancel)
#     check_csrf = False
# 
#     def get_schema(self):
#         return createSchema('ContactSchema')
# 
#     def get_recipients(self):
#         recipients = []
#         for userid in find_role_userids(self.context, ROLE_MODERATOR):
#             user = self.api.get_user(userid)
#             email = user.get_field_value('email')
#             if email:
#                 recipients.append(email)
#         if not recipients:
#             for userid in find_authorized_userids(self.context, (MODERATE_MEETING,)):
#                 user = self.api.get_user(userid)
#                 email = user.get_field_value('email')
#                 if email:
#                     recipients.append(email)
#         return recipients
# 
#     def send_success(self, appstruct):
#         if appstruct.get('email', None):
#             sender = appstruct['email']
#             if self.api.user_profile:
#                 sender += " <%s>" % self.api.user_profile.title
#         else:
#             sender = None
#         response = {'api': self.api,
#                     'meeting': self.api.meeting,
#                     'name': appstruct['name'],
#                     'email': appstruct['email'],
#                     'subject': appstruct['subject'],
#                     'message': appstruct['message'],
#                     'meeting_title': appstruct.get('meeting_title', ''),}
#         body_html = render('templates/email/help_contact.pt', response, request = self.request)
#         subject = "[%s] %s" % (self.context.title, appstruct['subject'])
#         recipients = self.get_recipients()
#         send_email(subject, recipients, body_html, sender = sender, request = self.request)
#         self.api.flash_messages.add(_(u"Message sent to the moderators"))
#         url = self.request.resource_url(self.context)
#         return HTTPFound(location = url)
# 
# 
# @view_config(name = 'support',
#              context = ISiteRoot,
#              renderer = "voteit.core.views:templates/base_edit.pt",
#              permission = NO_PERMISSION_REQUIRED)
# @view_config(name = 'support',
#              context = IMeeting,
#              renderer = "voteit.core.views:templates/base_edit.pt",
#              permission = security.VIEW)
# class SupportForm(BaseForm):
#     buttons = (button_send, button_cancel)
#     check_csrf = False
# 
#     def __call__(self):
#         support_email = self.api.root.get_field_value('support_email', None)
#         if not support_email:
#             self.api.flash_messages.add(_(u"No support email set for this site. Form won't work!"))
#             url = self.request.resource_url(self.context)
#             raise HTTPForbidden(location = url)
#         return super(SupportForm, self).__call__()
# 
#     def get_schema(self):
#         return createSchema('SupportSchema')
# 
#     def send_success(self, appstruct):
#         sender = appstruct['email'] and appstruct['email'] or "VoteIT <noreply@voteit.se>"
#         response = {'api': self.api,
#                     'meeting': self.api.meeting,
#                     'name': appstruct['name'],
#                     'email': appstruct['email'],
#                     'subject': appstruct['subject'],
#                     'message': appstruct['message'],
#                     'meeting_title': appstruct.get('meeting_title', ''),}
#         body_html = render('templates/email/support.pt', response, request = self.request)
#         title = "%s %s" % (self.api.root.get_field_value('site_title', u"VoteIT"), self.api.translate(_(u"Support")))
#         subject = "[%s] | %s" % (title, appstruct['subject'])
#         support_email = self.api.root.get_field_value('support_email')
#         send_email(subject, [support_email], body_html, sender = sender, request = self.request)
#         self.api.flash_messages.add(_(u"Message sent"))
#         return HTTPFound(location = self.request.resource_url(self.context))
