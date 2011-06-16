from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.renderers import get_renderer
from pyramid.traversal import find_root, find_interface
from pyramid.exceptions import Forbidden
from zope.component import queryUtility
from zope.component.interfaces import ComponentLookupError

from deform import Form
from deform.exception import ValidationFailure
from webob.exc import HTTPFound

from voteit.core.views.api import APIView
from voteit.core.security import EDIT, VIEW
from voteit.core.models.interfaces import IPoll
from voteit.core.models.schemas import add_csrf_token


class PollView(object):
    """ View class for poll objects """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = APIView(context, request)

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
            
            self.context.set_poll_settings(appstruct)
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = self.form.render(appstruct=appstruct)
        return self.response
        
    @view_config(context=IPoll, renderer='templates/poll.pt', permission=VIEW)
    def poll_view(self):
        """ Render poll view.
        """
        #FIXME: Workflow states and explanatory text
        
        self.response['poll_result'] = self.context.render_poll_result()
        return self.response
    
