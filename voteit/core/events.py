from arche.events import ObjectUpdatedEvent #API b/c
from zope.interface import implementer
from zope.component.event import objectEventNotify

from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.interfaces import IObjectUpdatedEvent


@implementer(IWorkflowStateChange)
class WorkflowStateChange(object):
    
    def __init__(self, object, old_state, new_state):
        self.object = object
        self.old_state = old_state
        self.new_state = new_state
        #Delegate to updated event since VoteITs version of this event should be removed
        objectEventNotify(ObjectUpdatedEvent(object))
