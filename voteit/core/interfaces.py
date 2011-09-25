from zope.interface import Interface
from zope.interface import Attribute

#Events
class IWorkflowStateChange(Interface):
    """ An object event for a workflow state change. Used by IWorkflowAware. """
    object = Attribute("Object this event is for")
    old_state = Attribute("Old state id")
    new_state = Attribute("New state id")

    def __init__(object, old_state, new_state):
        """ Create event. """


class IObjectUpdatedEvent(Interface):
    """ An object event for object updated.
        Note that indexes and metadata can be set to make catalog indexing go faster.
    """
    object = Attribute("Object this event is for")
    indexes = Attribute("List of indexes that should be updated. Note: An empty list means all!")
    metadata = Attribute("Update metadata? Defaults to True")
    
    def __init__(object, indexes=(), metadata=True):
        """ Create event. """
        