from arche.events import ObjectUpdatedEvent #API b/c
from zope.interface import implements

from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.interfaces import IObjectUpdatedEvent



class WorkflowStateChange(object):
    implements(IWorkflowStateChange)
    
    def __init__(self, object, old_state, new_state):
        self.object = object
        self.old_state = old_state
        self.new_state = new_state
