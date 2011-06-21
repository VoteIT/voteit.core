from zope.interface import Interface
from zope.interface import Attribute

#Events
class IWorkflowStateChange(Interface):
    """ An object event for a workflow state change. Used by IWorkflowAware. """
    object = Attribute("Object this event is for")
    old_state = Attribute("Old state id")
    new_state = Attribute("New state id")
    
class IObjectUpdatedEvent(Interface):
    """ An object event for object updated. """
    object = Attribute("Object this event is for")

#Adapters
class ICatalogMetadata(Interface):
    """ An adapter to fetch metadata for the catalog.
        it adapts voteit.core.models.interfaces.ICatalogMetadataEnabled
        which is just a marker interface.
    """
    