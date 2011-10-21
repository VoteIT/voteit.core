from repoze.folder.interfaces import IObjectAddedEvent
from repoze.folder.interfaces import IObjectRemovedEvent
from zope.component.event import objectEventNotify
from pyramid.traversal import find_interface
from pyramid.events import subscriber

from voteit.core.models.interfaces import IVote
from voteit.core.models.interfaces import IPoll
from voteit.core.events import ObjectUpdatedEvent
from voteit.core.interfaces import IObjectUpdatedEvent


@subscriber([IVote, IObjectAddedEvent])
@subscriber([IVote, IObjectRemovedEvent])
@subscriber([IVote, IObjectUpdatedEvent])
def reindex_metadata_for_poll(obj, event):
    """ When a Vote is added, metadata and voted_userids for the poll should be updated. """
    poll = find_interface(obj, IPoll)
    assert poll
    poll_event = ObjectUpdatedEvent(poll, indexes = ('voted_userids',), metadata = True)
    objectEventNotify(poll_event)
