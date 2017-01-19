from BTrees.LOBTree import LOBTree
from arche.utils import utcnow
from persistent import Persistent
from zope.component import adapts
from zope.interface import implements

from voteit.core import VoteITMF as _
from voteit.core.models.arche_compat import createContent
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import ILogEntry
from voteit.core.models.interfaces import ILogHandler

#DEPRECATED - keep for b/c

class LogHandler(object):
    """ An adapter for :mod:`voteit.core.models.interfaces.IBaseContent`
        that handle logging. It's currently used to adapt site root and meeting.
        See :mod:`voteit.core.models.interfaces.ILogHandler`.
    """
    implements(ILogHandler)
    
    def __init__(self, context):
        self.context = context
    
    @property
    def log_storage(self):
        try:
            return self.context.__log_storage__
        except AttributeError:
            #For speed
            self.context.__log_storage__ = LOBTree()
            return self.context.__log_storage__
    
    def _next_free_key(self):
        if len(self.log_storage) == 0:
            return 0
        return self.log_storage.maxKey()+1
    
    def add(self, context_uid, message, tags=(), userid=None, scripted=None):
        obj = createContent('LogEntry', context_uid, message, tags=tags,
                            userid=userid, scripted=scripted)
        
        for i in range(10):
            k = self._next_free_key()
            if self.log_storage.insert(k, obj):
                return
        
        raise KeyError("Couln't find a free key for logging handler after 10 retries.") #pragma : no cover


#DEPRECATED - keep for b/c


class LogEntry(Persistent):
    implements(ILogEntry)

    def __init__(self, context_uid, message, tags=(), userid=None, scripted=None):
        self.created = utcnow()
        self.context_uid = context_uid
        self.message = message
        self.tags = tuple(tags)
        self.userid = userid
        self.scripted = scripted


# def includeme(config):
#     """ Include to activate log components.
#         like: config.include('voteit.core.models.logs')
#     """
#     #Register LogHandler adapter
#     config.registry.registerAdapter(LogHandler, (IBaseContent,), ILogHandler)

        