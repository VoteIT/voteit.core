

class BaseView(object):
    """ Base view class. Will be removed - use arche.views.base.BaseView"""
        
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.response = {}
        #self.response['api'] = self.api = APIView(context, request)
        #self.api.include_needed(context, request, self)
