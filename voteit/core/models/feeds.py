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
    """
    implements(IFeedHandler)
    
    def __init__(self, context):
        self.context = context
    
    @property
    def feed_storage(self):
        if not hasattr(self.context, '__feed_storage__'):
            self.context.__feed_storage__ = LOBTree()
        return self.context.__feed_storage__
    
    def _next_free_key(self):
        if len(self.feed_storage) == 0:
            return 0
        return self.feed_storage.maxKey()+1
    
    def add(self, context_uid, message, tags=(), url=None, guid=None):
        """ Add a feed entry.
            context_uid: the uid of the object that triggered the entry.
            message: the message to store.
            tags: list of tags, works as a feed category
            userid: if a user triggered the event, which user did so.
            scripted: if a script triggered the event, store script name here
        """
        obj = createContent('FeedEntry', context_uid, message, tags=tags,
                            url=url, guid=guid)
        
        for i in range(10):
            k = self._next_free_key()
            if self.feed_storage.insert(k, obj):
                return
        
        raise KeyError("Couln't find a free key for feed handler after 10 retries.")


@content_factory('FeedEntry', title=_(u"Feed entry"))
class FeedEntry(Persistent):
    implements(IFeedEntry)

    def __init__(self, context_uid, message, tags=(), url=None, guid=None):
        self.created = utcnow()
        self.context_uid = context_uid
        self.message = message
        self.tags = tuple(tags)
        self.url = url
        self.guid = guid


def includeme(config):
    """ Include to activate feed components.
        like: config.include('voteit.core.models.feedss')
    """
    #Register FeedHandler adapter
    config.registry.registerAdapter(FeedHandler, (IMeeting,), IFeedHandler)

        