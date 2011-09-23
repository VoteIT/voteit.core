from pyramid.view import view_config

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import ILogHandler
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.security import VIEW


LOG_TEMPLATE = "templates/logs.pt"


class LogsView(BaseView):

    @view_config(name="logs", context=IMeeting, renderer=LOG_TEMPLATE, permission=VIEW)
    @view_config(name="logs", context=ISiteRoot, renderer=LOG_TEMPLATE, permission=VIEW)
    def logs_view(self):
        log_handler = self.request.registry.getAdapter(self.context, ILogHandler)
        self.response['entries'] = log_handler.log_storage.values()
        self.response['dt_format'] = self.api.dt_util.dt_format
        
        return self.response