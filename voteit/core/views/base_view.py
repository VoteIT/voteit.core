from pyramid.view import view_config

from voteit.core.views.api import APIView
from voteit.core.security import VIEW
from voteit.core.models.interfaces import IBaseContent
from voteit.core import fanstaticlib
from voteit.core import VoteITMF as _


class BaseView(object):
    """ Base view class. Subclass this."""
        
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.response = {}
        self.response['api'] = self.api = APIView(context, request)
        self.api.include_needed(context, request, self)
        try:
            if self.api.meeting_state == 'upcoming':
                msg = _(u"This meeting hasn't started yet.")
                self.api.flash_messages.add(msg, type = 'lock')
            if self.api.meeting_state == 'closed':
                msg = _(u"This meeting has closed.")
                self.api.flash_messages.add(msg, type = 'lock')
        except:
            pass


class DefaultView(BaseView):
    """ Default view when something doesn't have a specific view registered. """

    @view_config(context=IBaseContent, renderer="templates/base_view.pt", permission=VIEW)
    def dynamic_view(self):
        return self.response
