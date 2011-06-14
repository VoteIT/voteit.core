from zope.interface import Interface
from zope.interface import Attribute

#Events
class IWorkflowStateChange(Interface):
    """ An event for a workflow state change. Used by IWorkflowAware. """
    object = Attribute("Object that changed state")
    old_state = Attribute("Old state id")
    new_state = Attribute("New state id")