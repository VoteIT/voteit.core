from pyramid.view import view_config

from voteit.core.models.interfaces import ISiteRoot
from voteit.core.security import VIEW


@view_config(context=ISiteRoot, name="config.js", permission=VIEW, renderer='templates/snippets/config.js.pt')
def javascript_config(request):
    #Note that self.request.response is not the same as self.response which is our dict
    request.response.content_type = 'text/javascript;;charset=utf-8'
    return {}
