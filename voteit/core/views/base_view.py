from pyramid.view import view_config

from voteit.core.views.api import APIView
from voteit.core.security import VIEW

DEFAULT_TEMPLATE = "templates/base_view.pt"


class BaseView(object):
    """ View class for generic objects """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = self.api = APIView(context, request)

    @view_config(renderer=DEFAULT_TEMPLATE, permission=VIEW)
    def dynamic_view(self):
        """ """
        return self.response
