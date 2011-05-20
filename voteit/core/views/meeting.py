from pyramid.view import view_config

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.security import VIEW

class MeetingView(BaseView):
    """ View for agenda items. """
    
    @view_config(context=IMeeting, renderer="templates/meeting.pt", permission=VIEW)
    def meeting_view(self):
        """ """
        #FIXME: this is just placeholders, should be filled with real data
        self.response['logged_in_participants'] = 5
        self.response['number_of_proposals'] = 32
        self.response['next_poll'] = '3 hours'
        self.response['remaining_meeting_time'] = '2 days, 3 hours'
        
        return self.response
