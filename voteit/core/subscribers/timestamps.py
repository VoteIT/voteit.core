from datetime import datetime

from pyramid.events import subscriber

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.interfaces import IWorkflowStateChange


@subscriber(IAgendaItem, IWorkflowStateChange)
def add_ai_timestamp(obj, event):
    """ Add timestamps when and ai is opened or closed. """
    
    if event.new_state == 'inactive':
        #To clear if the state was moved from active to inactive
        obj.set_field_value('start_time', None)
    
    if event.new_state == 'active':
        obj.set_field_value('start_time', datetime.now())
        obj.set_field_value('end_time', None)
    
    if event.new_state == 'closed':
        obj.set_field_value('end_time', datetime.now())
