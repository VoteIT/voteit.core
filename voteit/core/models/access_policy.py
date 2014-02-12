import deform
from zope.interface import implementer
from zope.component import adapter

from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_save
from voteit.core.models.schemas import button_request_access


@implementer(IAccessPolicy)
@adapter(IMeeting)
class AccessPolicy(object):
    """ See :mod:`voteit.core.models.interfaces.IAccessPolicy`.
    """
    name = None
    title = None
    description = None
    configurable = False
    view = False

    def __init__(self, context):
        self.context = context

    def is_public(self):
        return False

    def render_view(self, api):
        pass

    def schema(self, api):
        pass

    def form(self, api):
        schema = self.schema(api)
        schema = schema.bind(api = api, context = self.context, request = api.request)
        return deform.Form(schema, buttons = (button_request_access, button_cancel))

    def handle_success(self, api, appstruct):
        pass

    def config_schema(self, api):
        pass

    def config_form(self, api):
        schema = self.config_schema(api)
        if schema:
            schema = schema.bind(api = api, context = self.context, request = api.request)
            form = deform.Form(schema, buttons = (button_save, button_cancel,))
            return form
