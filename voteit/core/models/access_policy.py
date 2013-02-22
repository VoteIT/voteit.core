import deform
from zope.interface import implements
from zope.component import adapts

from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_save


class AccessPolicy(object):
    """ See :mod:`voteit.core.models.interfaces.IAccessPolicy`.
    """
    implements(IAccessPolicy)
    adapts(IMeeting)
    name = None
    title = None
    description = None
    configurable = False

    def __init__(self, context):
        self.context = context

    def is_public(self):
        return False

    def view(self, api):
        raise NotImplementedError("Must be implementet by subclass")

    def view_submit(self, api):
        pass

    def config_schema(self, api, **kw):
        pass

    def config_form(self, schema):
        form = deform.Form(schema, buttons = (button_save, button_cancel,))
        return form
