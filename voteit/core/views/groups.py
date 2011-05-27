
from pyramid.view import view_config
from pyramid.renderers import get_renderer
from pyramid.traversal import find_root, find_interface
from pyramid.url import resource_url
from pyramid.security import has_permission

import colander
from deform import Form
from deform.exception import ValidationFailure
from webob.exc import HTTPFound

from voteit.core.views.api import APIView
from voteit.core.security import MANAGE_GROUPS
from voteit.core.models.security_aware import get_groups_schema
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.schemas import add_csrf_token

DEFAULT_TEMPLATE = "templates/base_edit.pt"


class EditGroups(object):
    """ View class for adding, editing or deleting dynamic content. """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = self.api = APIView(context, request)


    @view_config(context=ISiteRoot, name="edit_groups", renderer=DEFAULT_TEMPLATE, permission=MANAGE_GROUPS)
    @view_config(context=IMeeting, name="edit_groups", renderer=DEFAULT_TEMPLATE, permission=MANAGE_GROUPS)
    def root_group_form(self):
        schema = get_groups_schema(self.context)
        add_csrf_token(self.context, self.request, schema)

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
            
            #Set permissions
            self.context.update_from_form(appstruct['userids_and_groups'])
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        appstruct = self.context.get_security_appstruct()
        
        self.response['form'] = self.form.render(appstruct=appstruct)
        return self.response
