from betahaus.pyracont.factories import createSchema
from deform import Form
from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPRedirection
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.url import resource_url
from pyramid.view import view_config

from voteit.core import fanstaticlib
from voteit.core import security
from voteit.core.helpers import ajax_options
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_save
from voteit.core.models.schemas import button_cancel
from voteit.core.views.base_view import BaseView
from voteit.core import VoteITMF as _


class SiteView(BaseView):
    
    @view_config(name="recaptcha", context=ISiteRoot, renderer="templates/base_edit.pt", permission = security.EDIT)
    def recaptcha(self):
        schema = createSchema("CaptchaSiteRootSchema").bind(context=self.context, request=self.request)
        
        add_csrf_token(self.context, self.request, schema)
            
        form = Form(schema, buttons=(button_save, button_cancel), use_ajax=True, ajax_options=ajax_options)
        self.api.register_form_resources(form)
        fanstaticlib.jquery_form.need()

        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                if self.request.is_xhr:
                    return Response(render("templates/ajax_edit.pt", self.response, request = self.request))
                
                return self.response
            
            self.context.set_field_appstruct(appstruct)
            
            url = resource_url(self.context, self.request)
            if self.request.is_xhr:
                return Response(headers = [('X-Relocate', url)])
            return HTTPFound(location=url)

        #FIXME: with ajax post this does not work no, we'll need to fix this
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))

            url = resource_url(self.context, self.request)
            if self.request.is_xhr:
                return Response(headers = [('X-Relocate', url)])
            return HTTPFound(location=url)

        #No action - Render form
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = form.render(appstruct)
        return self.response
