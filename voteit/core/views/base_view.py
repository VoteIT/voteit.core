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
        fanstaticlib.qtip.need()
        if self.api.show_moderator_actions or context.content_type == 'AgendaItem':
            #Easy confirm is used by retract proposal and wf menu actions
            fanstaticlib.voteit_workflow_js.need()
        fanstaticlib.voteit_main_css.need()
        fanstaticlib.voteit_common_js.need()
        if context.content_type == 'AgendaItem':
            #This is the only place we use inline info in now. That might change
            fanstaticlib.voteit_user_inline_info_js.need()


class DefaultView(BaseView):
    """ Default view when something doesn't have a specific view registered. """

    @view_config(context=IBaseContent, renderer="templates/base_view.pt", permission=VIEW)
    def dynamic_view(self):
        return self.response
