from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.renderers import get_renderer
from pyramid.traversal import find_root, find_interface

from deform import Form
from deform.exception import ValidationFailure
from webob.exc import HTTPFound

from voteit.core.views.api import APIView
from voteit.core.models.interfaces import IPoll


class BaseView(object):
    """ View class for generic objects """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.poll_plugin = self.context.poll_plugin

        self.response = {}
        self.response['api'] = APIView(context, request)

    @view_config(context=IPoll, name="poll_config", renderer='templates/base_edit.pt')
    def poll_config(self):
        """ Configure poll settings. Only for moderators.
            The settins themselves come from the poll plugin.
        """
        schema = self.poll_plugin.get_settings_schema(self.context)
        
        #Make the current value the default value
        for field in schema:
            field.default = self.context.get_field_value(field.name)

        self.form = Form(schema, buttons=('save', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = self.form.validate(controls)
                #FIXME: validate name - it must be unique and url-id-like
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            for (k, v) in appstruct.items():
                self.context.set_field_value(k, v)
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        return self.response
        
    @view_config(context=IPoll, renderer='templates/poll.pt')
    def poll_view(self):
        """ Render poll view. It has several functions:
            - It allows voters to vote in an ongoing poll.
            - It allows everyone to see the result of a closed poll.
        """
        schema = self.poll_plugin.get_poll_schema(self.context)
        
        #Make the current value the default value
        for field in schema:
            field.default = self.context.get_field_value(field.name)

        self.form = Form(schema, buttons=('vote', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'vote' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = self.form.validate(controls)
                #FIXME: validate name - it must be unique and url-id-like
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            #FIXME: Don't do anything yet
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response