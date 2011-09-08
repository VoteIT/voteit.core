from pyramid.exceptions import Forbidden
from pyramid.view import view_config
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.response import Response
from pyramid.security import authenticated_userid
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.url import resource_url

from webob.exc import HTTPFound

from voteit.core import security

from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem

from voteit.core.views.api import APIView


class ForbiddenView(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.api = APIView(request.context, request)
    
    @view_config(context=Forbidden)
    def forbidden_view(self):
        # is user logged in
        if self.api.userid:
            # find the meeting and make sure the user has permissoin to view it and redirect the user
            meeting = find_interface(self.request.context, IMeeting)
            if meeting and self.api.context_has_permission(security.VIEW, meeting):
                url = resource_url(meeting, self.request)
                return HTTPFound(location=url)

            # find siteroot and redirect the user
            root = find_root(self.request.context)
            if root:
                url = resource_url(root, self.request)
                return HTTPFound(location=url)
        else:
            return HTTPFound(location="%s/@@login?came_from=%s" %(self.request.application_url,self.request.url))
