from zope.interface import Interface
from zope.interface import Attribute
from repoze.folder.interfaces import IObjectAddedEvent #API
from repoze.folder.interfaces import IObjectRemovedEvent #API
from repoze.folder.interfaces import IObjectWillBeAddedEvent #API
from repoze.folder.interfaces import IObjectWillBeRemovedEvent #API
from arche.interfaces import IObjectUpdatedEvent #API


#Events
class IWorkflowStateChange(Interface):
    """ An object event for a workflow state change. Used by IWorkflowAware. """
    object = Attribute("Object this event is for")
    old_state = Attribute("Old state id")
    new_state = Attribute("New state id")

    def __init__(object, old_state, new_state):
        """ Create event. """
