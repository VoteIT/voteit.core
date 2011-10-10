from pyramid.view import view_config

from voteit.core.models.interfaces import ISiteRoot
from voteit.core.views.base_view import BaseView
from voteit.core.security import VIEW


class JavaScript(BaseView):
    
    @view_config(context=ISiteRoot, name="config.js", permission=VIEW, renderer='../static/config.js.pt')
    def javascript_config(self):
        #Note that self.request.response is not the same as self.response which is our dict
        self.request.response.content_type = 'text/javascript;;charset=utf-8'
        return self.response
