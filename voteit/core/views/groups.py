import os

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

from deform import ZPTRendererFactory
from pkg_resources import resource_filename

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__).decode('utf-8'))
mytemplates_path = os.path.join(CURRENT_PATH, 'templates/userlisting')

deform_templates = resource_filename('deform', 'templates')
search_path = (mytemplates_path, deform_templates)
renderer = ZPTRendererFactory(search_path)

class EditGroups(object):
    """ View class for adding, editing or deleting dynamic content. """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = self.api = APIView(context, request)


    def get_security_appstruct(self, context):
        """ Return the current settings in a structure that is usable in a deform form.
        """
        root = find_root(context)
        users = root['users']
        appstruct = {}
        userids_and_groups = []
        for userid in context._groups:
            user = users[userid]
            userids_and_groups.append({'userid':userid, 'groups':context.get_groups(userid), 'email':user.get_field_value('email')})
        appstruct['userids_and_groups'] = userids_and_groups
        return appstruct

    def get_security_and_invitations_appstruct(self, context):
        """ Return the current settings in a structure that is usable in a deform form,
            including invitations.
        """
        root = find_root(context)
        users = root['users']
        appstruct = {}
        userids_and_groups = []
        invitations_and_groups = []
        for userid in context._groups:
            user = users[userid]
            userids_and_groups.append({'userid':userid, 'groups':context.get_groups(userid), 'email':user.get_field_value('email')})
        for ticket in context.invite_tickets.values():
            if ticket.get_workflow_state() != u'closed':
                invitations_and_groups.append({'email':ticket.email, 'groups':tuple(ticket.roles)})
        appstruct['userids_and_groups'] = userids_and_groups

        appstruct['invitations_and_groups'] = invitations_and_groups
        return appstruct

    @view_config(context=IMeeting, name="edit_permissions", renderer=DEFAULT_TEMPLATE, permission=MANAGE_GROUPS)
    @view_config(context=ISiteRoot, name="edit_groups", renderer=DEFAULT_TEMPLATE, permission=MANAGE_GROUPS)
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
            self.context.update_userids_permissions_from_form(appstruct['userids_and_groups'])
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        appstruct = self.context.get_security_appstruct()
        
        self.response['form'] = self.form.render(appstruct=appstruct)
        return self.response
        
    @view_config(context=IMeeting, name="edit_groups", renderer=DEFAULT_TEMPLATE, permission=MANAGE_GROUPS)
    def meeting_group_form(self):
        schema = get_groups_schema(self.context)
        add_csrf_token(self.context, self.request, schema)

        self.form = Form(schema, buttons=('save', 'cancel'), renderer=renderer)
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
            self.context.update_userids_permissions_from_form(appstruct['userids_and_groups'])
            self.context.update_tickets_permissions_from_form(appstruct['invitations_and_groups'])
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        appstruct = self.get_security_and_invitations_appstruct(self.context)
        
        self.response['form'] = self.form.render(appstruct=appstruct)
        return self.response
