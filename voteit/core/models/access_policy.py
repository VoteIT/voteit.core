from zope.interface import implementer
from zope.component import adapter
from pyramid.httpexceptions import HTTPFound

from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IMeeting


@implementer(IAccessPolicy)
@adapter(IMeeting)
class AccessPolicy(object):
    """ See :mod:`voteit.core.models.interfaces.IAccessPolicy`.
    """
    name = None
    title = None
    description = None
    view = None

    def __init__(self, context):
        self.context = context

    def schema(self):
        pass

    def handle_success(self, view, appstruct):
        pass

    def config_schema(self):
        pass

    def handle_config_success(self, view, appstruct):
        self.context.set_field_appstruct(appstruct)
        view.flash_messages.add(view.default_success)
        return HTTPFound(location = view.request.resource_url(self.context))
