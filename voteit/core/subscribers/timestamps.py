from arche.utils import utcnow

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPoll
from voteit.core.interfaces import IWorkflowStateChange


def add_close_timestamp(obj, event):
    """ Add timestamps when a meeting, ai or poll is closed. """
    #Note: Use set_field_appstruct since we want the IObjectUpdatedEvent to be sent so the catalog gets reindexed.
    if event.new_state == 'closed':
        obj.set_field_appstruct({'end_time': utcnow()})
    #Clear end time when something was moved from closed to something else, Ie reopened.
    if event.old_state == 'closed':
        obj.set_field_appstruct({'end_time': None})


def add_start_timestamp(obj, event):
    """ Add timestamps when a meeting, ai or poll is started. """
    #Note: Use set_field_appstruct since we want the IObjectUpdatedEvent to be sent so the catalog gets reindexed.
    if event.old_state == 'upcoming' and event.new_state == 'ongoing':
        obj.set_field_appstruct({'start_time': utcnow()})
    #Clear start_time if it is moved to upcoming again
    if event.old_state == 'ongoing' and event.new_state == 'upcoming':
        obj.set_field_appstruct({'start_time': None})


def includeme(config):
    config.add_subscriber(add_close_timestamp, [IAgendaItem, IWorkflowStateChange])
    config.add_subscriber(add_close_timestamp, [IMeeting, IWorkflowStateChange])
    config.add_subscriber(add_close_timestamp, [IPoll, IWorkflowStateChange])
    config.add_subscriber(add_start_timestamp, [IAgendaItem, IWorkflowStateChange])
    config.add_subscriber(add_start_timestamp, [IMeeting, IWorkflowStateChange])
    config.add_subscriber(add_start_timestamp, [IPoll, IWorkflowStateChange])
