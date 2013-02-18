from pyramid.view import view_config
from pyramid.security import NO_PERMISSION_REQUIRED

from voteit.core.models.interfaces import ISiteRoot
from voteit.core.views.base_view import BaseView


class UnsupportedBrowser(BaseView):
    
    @view_config(context=ISiteRoot, name="unsupported_browser", renderer="templates/unsupported_browser.pt", permission=NO_PERMISSION_REQUIRED)
    def unsupported_browser(self):
        return self.response