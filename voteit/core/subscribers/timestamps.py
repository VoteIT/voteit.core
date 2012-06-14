from datetime import datetime

from pyramid.events import subscriber

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.models.date_time_util import DateTimeUtil


@subscriber([IAgendaItem, IWorkflowStateChange])
@subscriber([IMeeting, IWorkflowStateChange])
def add_close_timestamp(obj, event):
    """ Add timestamps when a meeting or an agenda item is closed. """
    dt_util = DateTimeUtil()
    #Note: Use set_field_appstruct since we want the IObjectUpdatedEvent to be sent so the catalog gets reindexed.
    if event.new_state == 'closed':
        obj.set_field_appstruct({'end_time': dt_util.utcnow()})
    #Clear end time when something was moved from closed to something else, Ie reopened.
    if event.old_state == 'closed':
        obj.set_field_appstruct({'end_time': None})

@subscriber([IAgendaItem, IWorkflowStateChange])
@subscriber([IMeeting, IWorkflowStateChange])
def add_start_timestamp(obj, event):
    """ Add timestamps when a meeting or an agenda item is started. """
    dt_util = DateTimeUtil()
    #Note: Use set_field_appstruct since we want the IObjectUpdatedEvent to be sent so the catalog gets reindexed.
    if event.old_state == 'upcoming' and event.new_state == 'ongoing':
        obj.set_field_appstruct({'start_time': dt_util.utcnow()})
    #Clear start_time if it is moved to upcoming again
    if event.old_state == 'ongoing' and event.new_state == 'upcoming':
        obj.set_field_appstruct({'start_time': None})
