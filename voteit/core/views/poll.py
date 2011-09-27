from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.renderers import get_renderer
from pyramid.traversal import find_root, find_interface
from pyramid.exceptions import Forbidden
from pyramid.response import Response
from zope.component import queryUtility
from zope.component.interfaces import ComponentLookupError
from deform import Form
from deform.exception import ValidationFailure
from webob.exc import HTTPFound
from zope.component.event import objectEventNotify

from voteit.core.views.api import APIView
from voteit.core import VoteITMF as _
from voteit.core.security import EDIT, VIEW
from voteit.core.models.interfaces import IPoll
from voteit.core.events import ObjectUpdatedEvent
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_update
from voteit.core.models.schemas import button_delete
from voteit.core.models.schemas import button_save


class PollView(object):
    """ View class for poll objects """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = self.api = APIView(context, request)
        
    @view_config(context=IPoll, name="edit", renderer='templates/base_edit.pt', permission=EDIT)
    def edit_form(self):
        content_type = self.context.content_type
        ftis = self.api.content_info
        schema = ftis[content_type].schema(context=self.context, request=self.request, type='edit')
        add_csrf_token(self.context, self.request, schema)

        self.form = Form(schema, buttons=(button_update, button_cancel))
        self.api.register_form_resources(self.form)

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

            updated = self.context.set_field_appstruct(appstruct)

            if updated:
                self.api.flash_messages.add(_(u"Successfully updated"))
                #TODO: This should probably not be fired here, instead it should be fired by the object
                objectEventNotify(ObjectUpdatedEvent(self.context))
            else:
                self.api.flash_messages.add(_(u"Nothing updated"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        msg = _(u"Edit")
        self.api.flash_messages.add(msg, close_button=False)
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = self.form.render(appstruct=appstruct)
        return self.response

    @view_config(context=IPoll, name="poll_config", renderer='templates/base_edit.pt', permission=EDIT)
    def poll_config(self):
        """ Configure poll settings. Only for moderators.
            The settings themselves come from the poll plugin.
            Note that the Edit permission should only be granted to moderators
            before the actual poll has been set in the ongoing state. After that,
            no settings may be changed.
        """
        poll_plugin = self.context.get_poll_plugin()
        schema = poll_plugin.get_settings_schema()
        if schema is None:
            raise Forbidden("No settings for this poll")
        add_csrf_token(self.context, self.request, schema)

        self.form = Form(schema, buttons=(button_save, button_cancel))
        self.api.register_form_resources(self.form)

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
            
            del appstruct['csrf_token'] #Otherwise it will be stored too
            self.context.poll_settings = appstruct
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        self.response['form'] = self.form.render(appstruct=self.context.poll_settings)
        return self.response
        
    @view_config(context=IPoll)
    def poll_view(self):
        """ Poll view should only redirect to parent agenda item!
        """
        url = resource_url(self.context.__parent__, self.request)
        return HTTPFound(location=url)
    
    @view_config(context=IPoll, name="poll_raw_data", permission=VIEW)
    def poll_raw_data(self):
        """ View for all ballots. See intefaces.IPollPlugin.render_raw_data
        """
        
        #Poll closed?
        if self.context.get_workflow_state() != 'closed':
            self.api.flash_messages.add("Poll not closed yet", type='error')
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)
        
        #This will generate a ComponentLookupError if the plugin isn't found,
        #however, that should never happen for a closed poll unless someone
        #removed the plugin.
        plugin = self.context.get_poll_plugin()
        return plugin.render_raw_data()
    
    @view_config(context=IPoll, name="state", renderer='templates/base_edit.pt')
    def state_change(self):
        """ Change workflow state for context.
            Note that if this view is called without the required permission,
            it will raise a WorkflowError exception. This view should
            never be linked to without doing the proper permission checks first.
            (Since the WorkflowError is not the same as Pyramids Forbidden exception,
            which will be handled by the application.)
        """
        state = self.request.params.get('state')
        self.context.set_workflow_state(self.request, state)
        
        url = resource_url(self.context.__parent__, self.request)
        return HTTPFound(location=url)
