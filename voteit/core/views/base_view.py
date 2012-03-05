from pyramid.view import view_config

from voteit.core.views.api import APIView
from voteit.core.security import VIEW
from voteit.core.models.interfaces import IBaseContent
from voteit.core import fanstaticlib


class BaseView(object):
    """ Base view class. Subclass this."""
        
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.response = {}
        self.response['api'] = self.api = APIView(context, request)
        if self.api.show_moderator_actions or context.content_type == 'AgendaItem':
            #Easy confirm is used by retract proposal and wf menu actions
            fanstaticlib.voteit_workflow_js.need()
        fanstaticlib.voteit_main_css.need()
        fanstaticlib.voteit_common_js.need()
        fanstaticlib.voteit_user_inline_info_js.need()
        fanstaticlib.voteit_deform.need() #FIXME: For help menus. This should be loaded dynamically instead!


class DefaultView(BaseView):
    """ Default view when something doesn't have a specific view registered. """

    @view_config(context=IBaseContent, renderer="templates/base_view.pt", permission=VIEW)
    def dynamic_view(self):
        return self.response
