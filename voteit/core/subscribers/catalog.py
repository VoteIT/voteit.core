from pyramid.traversal import find_interface
from pyramid.traversal import resource_path
from pyramid.events import subscriber
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.folder.interfaces import IObjectWillBeRemovedEvent

from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import ISiteRoot


@subscriber(IBaseContent, IObjectAddedEvent)
def index_object(obj, event):
    """ Index a base content object. """
    root = find_interface(obj, ISiteRoot)
    catalog = root.catalog
    
    obj_id = root.catalog.document_map.add(resource_path(obj))
    root.catalog.index_doc(obj_id, obj)

@subscriber(IBaseContent, IObjectUpdatedEvent)
@subscriber(IBaseContent, IWorkflowStateChange)
def reindex_object(obj, event):
    """ Reindex a base content object"""
    root = find_interface(obj, ISiteRoot)
    catalog = root.catalog
    
    obj_id = root.catalog.document_map.docid_for_address(resource_path(obj))
    root.catalog.reindex_doc(obj_id, obj)

@subscriber(IBaseContent, IObjectWillBeRemovedEvent)
def unindex_object(obj, event):
    """ Remove an index for a base content object"""
    root = find_interface(obj, ISiteRoot)
    catalog = root.catalog
    
    obj_id = root.catalog.document_map.docid_for_address(resource_path(obj))
    root.catalog.unindex_doc(obj_id)