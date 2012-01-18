from deform import Form
from deform.exception import ValidationFailure
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPRedirection
from pyramid.url import resource_url
from betahaus.pyracont.factories import createSchema

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_send

class HelpView(BaseView):
    @view_config(name = 'contact', context=IMeeting, renderer="templates/ajax_edit.pt", permission=security.VIEW)
    def contact(self):
        """ Contact moderators of the meeting
        """
        schema = createSchema('ContactSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)
            
        form = Form(schema, buttons=(button_send,))
        self.api.register_form_resources(form)

        post = self.request.POST

        if 'send' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            #FIXME: send message to moderators
            self.api.flash_messages.add(_(u"Message sent to the moderators"))

        #No action - Render form
        self.response['form'] = form.render()
        return self.response
        
    @view_config(name = 'support', context=ISiteRoot, renderer="templates/ajax_edit.pt", permission=NO_PERMISSION_REQUIRED)
    def contact(self):
        """ Support form
        """
        schema = createSchema('SupportSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)
            
        form = Form(schema, buttons=(button_send,))
        self.api.register_form_resources(form)

        post = self.request.POST

        if 'send' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            #FIXME: send message to moderators
            self.api.flash_messages.add(_(u"Message sent to VoteIT"))

        #No action - Render form
        self.response['form'] = form.render()
        return self.response
