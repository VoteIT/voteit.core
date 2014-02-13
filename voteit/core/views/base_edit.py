import urllib

from pyramid.view import view_config
from pyramid.security import has_permission
from pyramid.httpexceptions import HTTPForbidden
from pyramid.traversal import find_resource
import colander
from deform import Form
from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema

from voteit.core import VoteITMF as _
from voteit.core.security import EDIT
from voteit.core.security import DELETE
from voteit.core.security import MODERATE_MEETING
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import add_came_from
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_update
from voteit.core.models.schemas import button_delete
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.views.api import APIView
from voteit.core.helpers import generate_slug
from voteit.core.helpers import move_object


DEFAULT_TEMPLATE = "templates/base_edit.pt"


class BaseEdit(object):
    """ Default edit class. Subclass this to create edit views. """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.response = {}
        self.response['api'] = self.api = APIView(context, request)
        self.api.include_needed(context, request, self)


class DefaultEdit(BaseEdit):
    """ Default view class for adding, editing or deleting dynamic content. """

    @view_config(context=IBaseContent, name="add", renderer=DEFAULT_TEMPLATE)
    def add_form(self):
        content_type = self.request.params.get('content_type')
        tag = self.request.GET.get('tag', None)
        #Permission check
        add_permission = self.api.content_types_add_perm(content_type)
        if not has_permission(add_permission, self.context, self.request):
            raise HTTPForbidden("You're not allowed to add '%s' in this context." % content_type)
        factory = self.api.get_content_factory(content_type)
        schema_name = self.api.get_schema_name(content_type, 'add')
        schema = createSchema(schema_name).bind(context=self.context, request=self.request, api=self.api, tag=tag)        
        form = Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)
        if content_type == 'AgendaItem':
            self.response['tabs'] = self.api.render_single_view_component(self.context, self.request, 'tabs', 'manage_agenda')
        post = self.request.POST
        if 'add' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            kwargs = {}
            kwargs.update(appstruct)
            if self.api.userid:
                kwargs['creators'] = [self.api.userid]
            obj = createContent(content_type, **kwargs)
            name = self.generate_slug(obj.title)
            self.context[name] = obj
            #Only show message if new object isn't discussion or proposal
            if content_type not in ('DiscussionPost', 'Proposal',):
                self.api.flash_messages.add(_(u"Successfully added"))
            #Success, redirect
            url = self.request.resource_url(obj)
            if (content_type == 'Proposal' or content_type == 'DiscussionPost') and tag:
                url = self.request.resource_url(obj, query={'tag': tag})
            #Polls might have a special redirect action if the poll plugin has a settings schema:
            if content_type == 'Poll':
                if obj.get_poll_plugin().get_settings_schema() is not None:
                    url += 'poll_config'
                else:
                    url = self.request.resource_url(obj.__parent__, anchor = obj.uid)
                msg = _(u"private_poll_info",
                        default = u"The poll is created in private state, to show it the participants you have to change the state to upcoming.")
                self.api.flash_messages.add(msg)
            return HTTPFound(location=url)
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        #No action - Render add form
        self.response['form'] = form.render()
        return self.response

    @view_config(context=ISiteRoot, name="add", renderer=DEFAULT_TEMPLATE, request_param = "content_type=Meeting")
    def add_meeting(self):
        """ Custom view used when adding meetings.
            FIXME: We may want to use custom callbacks on add instead, rather than lots of hacks in views.
        """
        content_type = self.request.params.get('content_type')
        #Permission check
        add_permission = self.api.content_types_add_perm(content_type)
        if not has_permission(add_permission, self.context, self.request):
            raise HTTPForbidden("You're not allowed to add '%s' in this context." % content_type)
        factory = self.api.get_content_factory(content_type)
        schema_name = self.api.get_schema_name(content_type, 'add')
        schema = createSchema(schema_name)
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api=self.api)
        form = Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)
        post = self.request.POST
        if 'add' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            copy_users_and_perms = appstruct['copy_users_and_perms']
            del appstruct['copy_users_and_perms']
            kwargs = {}
            kwargs.update(appstruct)
            if self.api.userid:
                kwargs['creators'] = [self.api.userid]
            obj = createContent(content_type, **kwargs)
            name = self.generate_slug(obj.title)
            self.context[name] = obj
            if copy_users_and_perms:
                obj.copy_users_and_perms(copy_users_and_perms)
                self.api.flash_messages.add(_(u"Users and their permissions successfully copied"))
            else:
                self.api.flash_messages.add(_(u"Successfully added"))
            #Success, redirect
            url = self.request.resource_url(obj)
            return HTTPFound(location=url)
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        #No action - Render add form
        self.response['form'] = form.render()
        return self.response

    @view_config(context=IBaseContent, name="edit", renderer=DEFAULT_TEMPLATE, permission=EDIT)
    def edit_form(self):
        self.response['title'] = _(u"Edit %s" % self.api.translate(self.context.display_name))
        content_type = self.context.content_type
        schema_name = self.api.get_schema_name(content_type, 'edit')
        schema = createSchema(schema_name)
        add_csrf_token(self.context, self.request, schema)
        add_came_from(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api=self.api)
        form = Form(schema, buttons=(button_update, button_cancel))
        self.api.register_form_resources(form)

        post = self.request.POST
        if self.request.method == 'POST':
            came_from = None
            if 'update' in post:
                controls = post.items()
                try:
                    appstruct = form.validate(controls)
                except ValidationFailure, e:
                    self.response['form'] = e.render()
                    return self.response
                #Came from should not be stored either
                came_from = appstruct.pop('came_from', '')                
                updated = self.context.set_field_appstruct(appstruct)
                if updated:
                    self.api.flash_messages.add(_(u"Successfully updated"))
                else:
                    self.api.flash_messages.add(_(u"Nothing updated"))
            if 'cancel' in post:
                self.api.flash_messages.add(_(u"Canceled"))
            if came_from:
                url = urllib.unquote(came_from)
            elif self.context.content_type == 'Poll':
                url = self.request.resource_url(self.context.__parent__, anchor = self.context.uid)
            else:
                url = self.request.resource_url(self.context)
            return HTTPFound(location = url)

        #No action - Render edit form
        appstruct = self.context.get_field_appstruct(schema)
        came_from = self.request.GET.get('came_from', None)
        if came_from:
            appstruct['came_from'] = came_from
        self.response['form'] = form.render(appstruct=appstruct)
        return self.response

    @view_config(context=IBaseContent, name="delete", permission=DELETE, renderer=DEFAULT_TEMPLATE)
    def delete_form(self):
        """ Remove content """
        schema = colander.Schema()
        add_csrf_token(self.context, self.request, schema)
        add_came_from(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api=self.api)
        form = Form(schema, buttons=(button_delete, button_cancel))
        self.api.register_form_resources(form)
        post = self.request.POST
        if 'delete' in post:
            if self.context.content_type in ('SiteRoot', 'Users', 'User'):
                raise HTTPForbidden("Can't delete this content type")
            parent = self.context.__parent__
            del parent[self.context.__name__]
            self.api.flash_messages.add(_(u"Deleted"))
            url = self.request.resource_url(parent)
            came_from = self.request.POST.get('came_from', None)
            if came_from:
                url = urllib.unquote(came_from) 
            return HTTPFound(location=url)
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)

        #No action - Render edit form
        if self.context.content_type == 'Proposal':
            used_in_polls = []
            ai = self.context.__parent__
            for poll in ai.get_content(content_type = 'Poll'):
                if self.context.uid in poll.proposal_uids:
                    used_in_polls.append("'%s'" % poll.title)
            if used_in_polls:
                msg = _(u"deleting_proposals_used_in_polls_not_allowed_error",
                        default = u"You can't remove this proposal - it's used within the following polls: ${poll_titles}",
                        mapping = {'poll_titles': u", ".join(used_in_polls)})
                self.api.flash_messages.add(msg, type = 'error', close_button = False)
                raise HTTPFound(location = self.request.resource_url(ai))

        msg = _(u"delete_form_notice",
                default = u"Are you sure you want to delete '${display_name}' with title: ${title}?",
                mapping = {'display_name': self.api.translate(self.context.display_name),
                           'title': self.context.title})
        self.api.flash_messages.add(msg, close_button = False)
        appstruct = {}
        came_from = self.request.GET.get('came_from', None)
        if came_from:
            appstruct['came_from'] = came_from
            
        self.response['form'] = form.render(appstruct)
        return self.response

    def generate_slug(self, text, limit=40):
        """ Suggest a name for content that will be added.
            text is a title or similar to be used.
        """
        return generate_slug(self.context, text, limit)
        
    @view_config(context=IWorkflowAware, name="state")
    def state_change(self):
        """ Change workflow state for context.
            Note that if this view is called without the required permission,
            it will raise a WorkflowError exception. This view should
            never be linked to without doing the proper permission checks first.
            (Since the WorkflowError is not the same as Pyramids HTTPForbidden exception,
            which will be handled by the application.)
        """
        state = self.request.params.get('state')
        self.context.set_workflow_state(self.request, state)
        
        url = self.request.resource_url(self.context)
        return HTTPFound(location=url)

    @view_config(name = "move_object", context = IProposal, permission = MODERATE_MEETING,
                 renderer = DEFAULT_TEMPLATE)
    @view_config(name = "move_object", context = IDiscussionPost, permission = MODERATE_MEETING,
                 renderer = DEFAULT_TEMPLATE)
    def move_object(self):
        """ Move object to a new parent. """
        schema = createSchema('MoveObjectSchema')
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api=self.api)
        form = Form(schema, buttons=(button_update, button_cancel))

        post = self.request.POST
        if 'update' in post:
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            new_parent_path = urllib.unquote(appstruct['new_parent_path'])
            new_parent = find_resource(self.api.root, new_parent_path)
            context = move_object(self.context, new_parent)
            self.api.flash_messages.add(_(u"Moved"))
            url = self.request.resource_url(context)
            return HTTPFound(location=url)
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        self.response['form'] = form.render()
        return self.response
