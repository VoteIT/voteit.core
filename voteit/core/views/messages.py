from pyramid.view import view_config

from voteit.core.models.interfaces import IMeeting
from voteit.core.views.base_view import BaseView
from voteit.core.security import VIEW


class MessageView(BaseView):
    
    @view_config(context=IMeeting, name="messages", permission=VIEW, renderer='templates/messages.pt')
    def meeting_messages(self):
        self.response['messages'] = self.api.messages_adapter.retrieve_messages(self.context.uid, userid=self.api.userid)
        return self.response