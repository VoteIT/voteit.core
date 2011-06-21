from calendar import timegm

from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
from repoze.catalog.indexes.path import CatalogPathIndex
from pyramid.traversal import resource_path

from voteit.core.models.interfaces import IWorkflowAware

def update_indexes(catalog):
    indexes = {
        'title': CatalogFieldIndex(get_title),
        'sortable_title': CatalogFieldIndex(get_sortable_title),
        'uid': CatalogFieldIndex(get_uid),
        'content_type': CatalogFieldIndex(get_content_type),
        'workflow_state': CatalogFieldIndex(get_workflow_state),
        'path': CatalogPathIndex(get_path),
        'creators': CatalogKeywordIndex(get_creators),
        'created': CatalogFieldIndex(get_created),
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

def get_path(object, default):
    return resource_path(object)

def get_creators(object, default):
    return object.creators and tuple(object.creators) or ()

def get_created(object, default):
    """ The created time is stored in the catalog as unixtime.
        See the time.gmtime and calendar.timegm Python modules for more info.
        http://docs.python.org/library/calendar.html#calendar.timegm
        http://docs.python.org/library/time.html#time.gmtime
    """
    return timegm(object.created.timetuple())
