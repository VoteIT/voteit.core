from calendar import timegm

from arche.interfaces import ICataloger
from pyramid.security import principals_allowed_by_permission
from pyramid.traversal import find_resource
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
from zope.component.interfaces import ComponentLookupError

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.security import NEVER_EVER_PRINCIPAL
from voteit.core.security import VIEW
from voteit.core.security import find_authorized_userids
from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.models.interfaces import IBaseContent


def resolve_catalog_docid(catalog, root, docid):
    """ Takes a catalog docid and returns object that was indexed.
        This method should only be used when it's really necessary to have the object,
        since it will make it slower to retrieve objects.
    """
    #DEPRECATED
    path = root.document_map.address_for_docid(docid)
    if path is None:
        return ValueError("Nothing found in catalog with docid '%s'" % docid) # pragma : no cover
    return find_resource(root, path)

def get_aid(obj, default):
    """ Objects automatic id. """
    if IProposal.providedBy(obj):
        return obj.get_field_value('aid', default)
    return default

def get_aid_int(obj, default):
    if IProposal.providedBy(obj):
        return obj.get_field_value('aid_int', default)
    return default

def get_workflow_state(obj, default):
    """ Return workflow state, if this object has workflow enabled. """
    if not IWorkflowAware.providedBy(obj):
        return default
    return obj.get_workflow_state()

def get_allowed_to_view(obj, default):
    """ Return a list of all roles allowed to view this object. """
    principals = principals_allowed_by_permission(obj, VIEW)
    if not principals:
        # An empty value tells the catalog to match anything, whereas when
        # there are no principals with permission to view we want for there
        # to be no matches.
        principals = [NEVER_EVER_PRINCIPAL,]
    return principals

def get_view_meeting_userids(obj, default):
    """ Userids that are allowed to view a meeting. Only index meeting contexts. """
    if not IMeeting.providedBy(obj):
        return default
    try:
        userids = find_authorized_userids(obj, [VIEW])
        return userids and userids or default
    except ComponentLookupError: # pragma : no cover
        #This is to avoid having security fixture for each catalog test.
        return default

def get_start_time(obj, default):
    """ UNIX timestamp from start_time. """
    if IBaseContent.providedBy(obj):
        value = obj.get_field_value('start_time', default)
        if value and value != default:
            return timegm(value.timetuple())
    return default

def get_end_time(obj, default):
    """ UNIX timestamp from end_time. """
    if IBaseContent.providedBy(obj):
        value = obj.get_field_value('end_time', default)
        if value and value != default:
            return timegm(value.timetuple())
    return default


def get_searchable_prop_or_disc(context, default):
    if IProposal.providedBy(context) or IDiscussionPost.providedBy(context):
        return context.text
    return default


def update_contained_in_ai(obj, event):
    """ Special subscriber that touches any contained objects within
        agenda items when it changes wf stade to or from private.
        This is because some view permissions change on contained objects.
        They're cached in the catalog, and needs to be updated as well.
    """
    if event.old_state == 'private' or event.new_state == 'private':
        for o in obj.get_content(iface = IBaseContent):
            ICataloger(o).index_object()


def includeme(config):
    """ Register metadata adapter. """
    config.add_searchable_text_index('aid')
    config.add_searchable_text_discriminator(get_searchable_prop_or_disc)
    indexes = {
        'aid': CatalogFieldIndex(get_aid),
        'aid_int': CatalogFieldIndex(get_aid_int),
        'allowed_to_view': CatalogKeywordIndex(get_allowed_to_view),
        'view_meeting_userids': CatalogKeywordIndex(get_view_meeting_userids),
        'start_time' : CatalogFieldIndex(get_start_time),
        'end_time' : CatalogFieldIndex(get_end_time),
        'workflow_state': CatalogFieldIndex(get_workflow_state),
        '__name__': CatalogFieldIndex('__name__'),
    }
    config.add_catalog_indexes(__name__, indexes)
    config.add_subscriber(update_contained_in_ai, [IAgendaItem, IWorkflowStateChange])
    config.update_index_info('aid_int', linked='aid_int', type_names = 'Proposal')
    config.update_index_info('aid', type_names = 'Proposal')
    config.update_index_info('view_meeting_userids', type_names = 'Meeting')
