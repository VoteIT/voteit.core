from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.traversal import find_root, find_interface
from pyramid.url import resource_url

import colander
from deform import Form
from deform.exception import ValidationFailure
from webob.exc import HTTPFound

from voteit.core.models.factory_type_information import ftis
from voteit.core.views.api import APIView

DEFAULT_TEMPLATE = "templates/base_edit.pt"


class BaseEdit(object):
    """ View class for adding, editing or deleting dynamic content. """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = APIView(context, request)

    @view_config(name="add", renderer=DEFAULT_TEMPLATE)
    def add_form(self):
        content_type = self.request.params.get('content_type')
        ftis = self.response['api'].ftis
        schema = ftis[content_type].schema()

        self.form = Form(schema, buttons=('add', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'add' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = self.form.validate(controls)
                #FIXME: validate name - it must be unique and url-id-like
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            obj = ftis[content_type].type_class()
            for (k, v) in appstruct.items():
                obj.set_field_value(k, v)
            self.context[appstruct['name']] = obj
            
            url = resource_url(obj, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response

    @view_config(name="edit", renderer=DEFAULT_TEMPLATE)
    def edit_form(self):
        content_type = self.context.content_type
        ftis = self.response['api'].ftis
        schema = ftis[content_type].schema()
        
        #Remove unwanted fields like 'name'
        for omit_name in ftis[content_type].omit_fields_on_edit:
            if omit_name in schema:
                del schema[omit_name]

        #Make the current value the default value
        for field in schema:
            field.default = self.context.get_field_value(field.name)

        self.form = Form(schema, buttons=('update', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'update' in post:
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

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response

    @view_config(name="delete", renderer=DEFAULT_TEMPLATE)
    def delete_form(self):
        schema = colander.Schema()

        self.form = Form(schema, buttons=('delete', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'delete' in post:
            if self.context is self.root:
                raise Exception("Can't delete site root")

            parent = self.context.__parent__
            del parent[self.context.__name__]
            
            url = resource_url(parent, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response