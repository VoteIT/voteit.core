from arche.utils import utcnow
from arche.interfaces import IWorkflowAfterTransition

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPoll


def add_close_timestamp(obj, event):
    """ Add timestamps when a meeting, ai or poll is closed. """
    #Note: Use update since we want the IObjectUpdatedEvent to be sent so the catalog gets reindexed.
    if event.to_state == 'closed':
        obj.update(end_time=utcnow())
    #Clear end time when something was moved from closed to something else, Ie reopened.
    if event.from_state == 'closed':
        obj.update(end_time=None)


def add_start_timestamp(obj, event):
    """ Add timestamps when a meeting, ai or poll is started. """
    #Note: Use update since we want the IObjectUpdatedEvent to be sent so the catalog gets reindexed.
    if event.to_state == 'ongoing':
        obj.update(start_time=utcnow())
    #Clear start_time if it is moved to upcoming again
    if event.from_state == 'ongoing' and event.to_state == 'upcoming':
        obj.update(start_time=None)


def includeme(config):
    config.add_subscriber(add_close_timestamp, [IAgendaItem, IWorkflowAfterTransition])
    config.add_subscriber(add_close_timestamp, [IMeeting, IWorkflowAfterTransition])
    config.add_subscriber(add_close_timestamp, [IPoll, IWorkflowAfterTransition])
    config.add_subscriber(add_start_timestamp, [IAgendaItem, IWorkflowAfterTransition])
    config.add_subscriber(add_start_timestamp, [IMeeting, IWorkflowAfterTransition])
    config.add_subscriber(add_start_timestamp, [IPoll, IWorkflowAfterTransition])
