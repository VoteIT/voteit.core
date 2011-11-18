from zope.interface import implements
from BTrees.OOBTree import OOSet
from zope.component.event import objectEventNotify
from zope.component import adapts

from voteit.core.security import find_authorized_userids
from voteit.core.security import VIEW
from voteit.core.models.interfaces import IUnread
from voteit.core.events import ObjectUpdatedEvent


class Unread(object):
    """ Unread adapter. See :mod:`voteit.core.models.interfaces.IUnread`.
        All methods are documented in the interface of this class.
    """
    implements(IUnread)
    
    def __init__(self, context):
        self.context = context
    
    @property
    def unread_storage(self):
        try:
            return self.context.__unread_storage__
        except AttributeError: #This is basically init
            self.context.__unread_storage__ = OOSet( find_authorized_userids(self.context, (VIEW, )) )
            return self.context.__unread_storage__

    def mark_as_read(self, userid):
        storage = self.unread_storage
        if userid in storage:
            storage.remove(userid)
            objectEventNotify(ObjectUpdatedEvent(self.context, indexes=('unread',), metadata=False))

    def get_unread_userids(self):
        return frozenset(self.unread_storage.keys())


def includeme(config):
    """ Register unread adapter. """
    from voteit.core.models.interfaces import IDiscussionPost
    from voteit.core.models.interfaces import IPoll
    from voteit.core.models.interfaces import IProposal
    config.registry.registerAdapter(Unread, (IDiscussionPost,), IUnread)
    config.registry.registerAdapter(Unread, (IPoll,), IUnread)
    config.registry.registerAdapter(Unread, (IProposal,), IUnread)


#FIXME: method to disable unread adapter?