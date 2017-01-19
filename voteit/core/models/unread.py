from BTrees.OOBTree import OOSet
from pyramid.traversal import find_interface
from zope.component import adapter
from zope.component.event import objectEventNotify
from zope.interface import implementer

from voteit.core.events import ObjectUpdatedEvent
from voteit.core.helpers import get_meeting_participants
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IUnread


@implementer(IUnread)
class Unread(object):
    """ Unread adapter. See :mod:`voteit.core.models.interfaces.IUnread`.
        All methods are documented in the interface of this class.
    """
    def __init__(self, context):
        self.context = context
    
    @property
    def unread_storage(self):
        try:
            return self.context.__unread_storage__
        except AttributeError: #This is basically init
            meeting = find_interface(self.context, IMeeting)
            self.context.__unread_storage__ = OOSet( get_meeting_participants(meeting) )
            return self.context.__unread_storage__

    def mark_as_read(self, userid):
        if userid in self.unread_storage:
            self.unread_storage.remove(userid)
            objectEventNotify(ObjectUpdatedEvent(self.context, changed=('unread',)))

    def get_unread_userids(self):
        return frozenset(self.unread_storage.keys())
    
    def reset_unread(self):
        try:
            del self.context.__unread_storage__
            objectEventNotify(ObjectUpdatedEvent(self.context, changed=('unread',)))
        except AttributeError:
            pass


def includeme(config):
    """ Register unread adapter. """
    config.registry.registerAdapter(Unread, required = (IDiscussionPost,))
    config.registry.registerAdapter(Unread, required = (IProposal,))
