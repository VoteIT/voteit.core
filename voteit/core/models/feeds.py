from zope.component import adapts
from zope.interface import implements
from persistent import Persistent
from BTrees.LOBTree import LOBTree
from betahaus.pyracont.decorators import content_factory
from betahaus.pyracont.factories import createContent

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IFeedHandler
from voteit.core.models.interfaces import IFeedEntry
from voteit.core.models.date_time_util import utcnow
from voteit.core import VoteITMF as _


class FeedHandler(object):
    """ An adapter for IMeeting that handle feed entries.
        See :mod:`voteit.core.models.interfaces.IFeedHandler`.
        All methods are documented in the interface of this class.
    """
    implements(IFeedHandler)
    
    def __init__(self, context):
        self.context = context
    
    @property
    def feed_storage(self):
        #Note: Syntax here is optimised for speed.
        try:
            return self.context.__feed_storage__
        except AttributeError:
            self.context.__feed_storage__ = LOBTree()
            return self.context.__feed_storage__
    
    def _next_free_key(self):
        if len(self.feed_storage) == 0:
            return 0
        return self.feed_storage.maxKey()+1
    
    def add(self, context_uid, message, tags=(), context=None):
        obj = createContent('FeedEntry', context_uid, message, tags=tags)
        
        for i in range(10):
            k = self._next_free_key()
            if self.feed_storage.insert(k, obj):
                return
        
        raise KeyError("Couln't find a free key for feed handler after 10 retries.") # pragma : no cover


@content_factory('FeedEntry', title=_(u"Feed entry"))
class FeedEntry(Persistent):
    """ FeedEntry lightweight content type.
        See :mod:`voteit.core.models.interfaces.IFeedEntry`.
        All methods are documented in the interface of this class.
    """
    implements(IFeedEntry)

    def __init__(self, context_uid, message, tags=()):
        self.created = utcnow()
        self.context_uid = context_uid
        self.message = message
        self.tags = tuple(tags)


def includeme(config):
    """ Include to register FeedHandler adapter.
        like: config.include('voteit.core.models.feeds')
        FeedEntry will be picked up by the regular scan()-method.
    """
    config.registry.registerAdapter(FeedHandler, (IMeeting,), IFeedHandler)

        