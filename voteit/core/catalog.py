from repoze.catalog.indexes.field import CatalogFieldIndex
from voteit.core.models.interfaces import IWorkflowAware
from repoze.catalog.indexes.keyword import CatalogKeywordIndex


def update_indexes(catalog):
    indexes = {
        'title': CatalogFieldIndex(get_title),
        'sortable_title': CatalogFieldIndex(get_sortable_title),
        'uid': CatalogFieldIndex(get_uid),
        'content_type': CatalogFieldIndex(get_content_type),
        'workflow_state': CatalogFieldIndex(get_workflow_state),
    }
    
    # add indexes
    for name, index in indexes.iteritems():
        if name not in catalog:
            catalog[name] = index
    
    # remove indexes
    for name in catalog.keys():
        if name not in indexes:
            del catalog[name]


def get_title(object, default):
    return object.title

def get_sortable_title(object, default):
    return object.title.lower()

def get_uid(object, default):
    return object.uid

def get_content_type(object, default):
    return object.content_type

def get_workflow_state(object, default):
    if not IWorkflowAware.providedBy(object):
        return default
    return object.get_workflow_state()