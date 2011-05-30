from pyramid.security import has_permission
from pyramid.view import view_config
from webob.exc import HTTPFound
import deform
from pyramid.exceptions import Forbidden

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting


class MeetingView(BaseView):
    
    @view_config(context=IMeeting, renderer="templates/meeting.pt")
    def meeting_view(self):
        """ Meeting view behaves a bit differently than regular views since
            it should allow users to request access if unauthorized is raised.
        """
        if not has_permission(security.VIEW, self.context, self.request):
            self.api.flash_messages.add(_(u"You're not allowed access to this meeting."), type='error')
            
            url = self.api.resource_url(self.api.root, self.request)
            return HTTPFound(location = url)
            
            #FIXME:
            #If user is authenticated:
#            if has_permission(security.REQUEST_MEETING_ACCESS, self.context, self.request):
#                url = self.api.resource_url(self.context, self.request) + 'request_meeting_access'
#                return HTTPFound(location = url)
            
            #Otherwise raise unauthorized
            #raise Forbidden("You can't request access to this meeting. Maybe you need to login, or it isn't allowed.")
        
        #FIXME: this is just placeholders, should be filled with real data
        self.response['logged_in_participants'] = 5
        self.response['number_of_proposals'] = 32
        self.response['next_poll'] = '3 hours'
        self.response['remaining_meeting_time'] = '2 days, 3 hours'

        return self.response


