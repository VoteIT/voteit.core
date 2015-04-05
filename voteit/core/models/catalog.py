from calendar import timegm

from arche.interfaces import ICataloger
from arche.interfaces import IObjectAddedEvent
from arche.interfaces import IObjectWillBeRemovedEvent
from arche.models.catalog import Metadata
from pyramid.events import subscriber
from pyramid.security import principals_allowed_by_permission
from pyramid.traversal import find_interface
from pyramid.traversal import find_resource
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
from zope.component import adapter
from zope.component import getAdapter
from zope.component import queryAdapter
from zope.component.interfaces import ComponentLookupError
from webhelpers.html.render import sanitize

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IUnread
from voteit.core.models.interfaces import IUserTags
from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.security import NEVER_EVER_PRINCIPAL
from voteit.core.security import VIEW
from voteit.core.security import find_authorized_userids
from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import ISiteRoot


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

def metadata_for_query(root, **kwargs):
    """ Get metadata objects and return them. Shorthand for looking up
        metadata from a query result.
    """
    #FIXME: Is this deprecated?
    num, docids = root.catalog.search(**kwargs)
    metadata = [root.document_map.get_metadata(x) for x in docids]
    return tuple(metadata)

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

def get_unread(obj, default):
    """ All userids who have this object as unread. """
    unread = queryAdapter(obj, IUnread)
    if unread == None:
        return default
    userids = unread.get_unread_userids()
    if userids:
        return userids
    return default

def get_like_userids(obj, default):
    """ Returns all userids who 'like' something.
        We only use like for Discussions and Proposals.
        Warning! An empty list doesn't update the catalog.
        If default is returned to an index, it will cause that index to remove index,
        which is the correct behaviour for the catalog.
    """
    if IDiscussionPost.providedBy(obj) or IProposal.providedBy(obj):
        user_tags = getAdapter(obj, IUserTags)
        likes = user_tags.userids_for_tag('like')
        if likes:
            return likes
    return default

def get_order(obj, default):
    """ Return order, if object has that field. """
    if IBaseContent.providedBy(obj):
        return obj.get_field_value('order', default)
    return default

def get_searchable_prop_or_disc(context, default):
    if IProposal.providedBy(context) or IDiscussionPost.providedBy(context):
        return context.text
    return default

@subscriber([IBaseContent, IObjectWillBeRemovedEvent])
@subscriber([IBaseContent, IObjectAddedEvent])
def update_if_ai_parent(obj, event):
    """ Since AIs keep track of count of Poll, Proposal and Discussion objects.
        Only needed for add and remove.
    """
    parent = getattr(obj, '__parent__', None)
    if IAgendaItem.providedBy(parent):
        ICataloger(parent).index_object()

@subscriber([IAgendaItem, IWorkflowStateChange])
def update_contained_in_ai(obj, event):
    """ Special subscriber that touches any contained objects within
        agenda items when it changes wf stade to or from private.
        This is because some view permissions change on contained objects.
        They're cached in the catalog, and needs to be updated as well.
        
        Any index that has to do with view permissions on a contained object
        has to be touched. Currently:

         * allowed_to_view
    """
    if event.old_state == 'private' or event.new_state == 'private':
        indexes = ('allowed_to_view', )
        root = find_interface(obj, ISiteRoot)
        for o in obj.get_content(iface = IBaseContent):
            ICataloger(o).index_object()
            #reindex_object(root.catalog, o, indexes = indexes, metadata = False)


@adapter(IAgendaItem)
class _CountMetadata(object):

    def __call__(self, default=None):
        root = find_root(self.context)
        path = resource_path(self.context)
        return root.catalog.search(type_name = self.type_counter, path = path)[0].total


class ProposalCountMetadata(_CountMetadata, Metadata):
    name = 'proposal_count'
    type_counter = 'Proposal'


class DiscussionCountMetadata(_CountMetadata, Metadata):
    name = 'discussion_count'
    type_counter = 'DiscussionPost'


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
        'unread': CatalogKeywordIndex(get_unread),
        'like_userids': CatalogKeywordIndex(get_like_userids),
        'order': CatalogFieldIndex(get_order),
        'workflow_state': CatalogFieldIndex(get_workflow_state),
    }
    config.add_catalog_indexes(__name__, indexes)
    config.scan(__name__)

    config.create_metadata_field('title', 'title')
    config.create_metadata_field('__name__', '__name__')
    config.add_metadata_field(ProposalCountMetadata)
    config.add_metadata_field(DiscussionCountMetadata)
