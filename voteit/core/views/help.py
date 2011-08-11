from pyramid.view import view_config
from zope.component import getUtility

from voteit.core.security import VIEW
from voteit.core.models.interfaces import IHelpUtil


class Help(object):
    """ View class for generic objects """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.help_util = getUtility(IHelpUtil)
        
        self.response = {}

    @view_config(name="help", permission=VIEW, renderer='templates/help.pt')
    def dynamic_view(self):
        """ """
        self.response['help'] = self.help_util.get(self.request.GET['article'])
        
        return self.response
