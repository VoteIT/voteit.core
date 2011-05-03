from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.renderers import get_renderer
from pyramid.traversal import find_root, find_interface

from voteit.core.views.api import APIView

DEFAULT_TEMPLATE = "templates/base_view.pt"


class BaseView(object):
    """ View class for generic objects """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = APIView(context, request)
        self.response['show_content_listing'] = True

    @view_config(renderer=DEFAULT_TEMPLATE)
    def dynamic_view(self):
        """ """
        return self.response