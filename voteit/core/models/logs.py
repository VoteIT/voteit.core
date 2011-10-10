from zope.component import adapts
from zope.interface import implements
from persistent import Persistent
from BTrees.LOBTree import LOBTree
from betahaus.pyracont.decorators import content_factory
from betahaus.pyracont.factories import createContent

from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import ILogHandler
from voteit.core.models.interfaces import ILogEntry
from voteit.core.models.date_time_util import utcnow
from voteit.core import VoteITMF as _


class LogHandler(object):
    """ An adapter for IBaseContent that handle logging.
        It's currently used to adapt site root and meeting.
    """
    implements(ILogHandler)
    
    def __init__(self, context):
        self.context = context
    
    @property
    def log_storage(self):
        if not hasattr(self.context, '__log_storage__'):
            self.context.__log_storage__ = LOBTree()
        return self.context.__log_storage__
    
    def _next_free_key(self):
        if len(self.log_storage) == 0:
            return 0
        return self.log_storage.maxKey()+1
    
    def add(self, context_uid, message, tags=(), userid=None, scripted=None):
        """ Add a log entry.
            context_uid: the uid of the object that triggered logging.
            message: the message to store.
            tags: list of tags, works as a log category
            userid: if a user triggered the event, which user did so.
            scripted: if a script triggered the event, store script name here
        """
        obj = createContent('LogEntry', context_uid, message, tags=tags,
                            userid=userid, scripted=scripted)
        
        for i in range(10):
            k = self._next_free_key()
            if self.log_storage.insert(k, obj):
                return
        
        raise KeyError("Couln't find a free key for logging handler after 10 retries.")


@content_factory('LogEntry', title=_(u"Log entry"))
class LogEntry(Persistent):
    implements(ILogEntry)

    def __init__(self, context_uid, message, tags=(), userid=None, scripted=None):
        self.created = utcnow()
        self.context_uid = context_uid
        self.message = message
        self.tags = tuple(tags)
        self.userid = userid
        self.scripted = scripted


def includeme(config):
    """ Include to activate log components.
        like: config.include('voteit.core.models.logs')
    """
    #Register LogHandler adapter
    config.registry.registerAdapter(LogHandler, (IBaseContent,), ILogHandler)

        