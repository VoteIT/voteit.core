from zope.interface import Interface
from zope.interface import Attribute

#Events
class IWorkflowStateChange(Interface):
    """ An object event for a workflow state change. Used by IWorkflowAware. """
    object = Attribute("Object this event is for")
    old_state = Attribute("Old state id")
    new_state = Attribute("New state id")