from pyramid.view import view_config
from pyramid.url import resource_url

from webob.exc import HTTPFound

from voteit.core.views.api import APIView
from voteit.core import VoteITMF as _
from voteit.core.security import VIEW
from voteit.core.models.schemas import add_csrf_token
from voteit.core.events import ObjectUpdatedEvent

from voteit.core.models.unread import Unreads


class Unread(object):
    """ View class for managing unreads. """

    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = self.api = APIView(context, request)

    @view_config(name="read", permission=VIEW)
    def read(self):
        """ Mark the context as read for the user.
        """
        unreads = Unreads(self.request)
        unreads.remove(self.api.userid, self.context.uid)
        
        url = resource_url(self.context, self.request)
        return HTTPFound(location=url)
