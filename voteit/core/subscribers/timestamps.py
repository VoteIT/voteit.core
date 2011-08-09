from datetime import datetime

from pyramid.events import subscriber

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.interfaces import IWorkflowStateChange


@subscriber(IAgendaItem, IWorkflowStateChange)
@subscriber(IMeeting, IWorkflowStateChange)
def add_close_timestamp(obj, event):
    """ Add timestamps when a meeting or an agenda item is closed. """
    
    #Clear end time when something was moved from closed to something else, Ie reopened.
    if event.old_state == 'closed':
        obj.set_field_value('end_time', None)
    
    if event.new_state == 'closed':
        obj.set_field_value('end_time', datetime.now())
