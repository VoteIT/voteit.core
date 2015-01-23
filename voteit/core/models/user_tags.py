import re

from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOSet
from zope.interface import implements
from zope.component.event import objectEventNotify

from voteit.core.models.interfaces import IUserTags
from voteit.core.models.interfaces import IBaseContent
from voteit.core.events import ObjectUpdatedEvent

_TAG_STRING = r'^[a-zA-Z\_\-]{3,15}$'
TAG_PATTERN = re.compile(_TAG_STRING)


class UserTags(object):
    """ User tags adapter.
        See :mod:`voteit.core.models.interfaces.IUserTags`.
        All methods are documented in the interface of this class.
    """
    implements(IUserTags)
    
    def __init__(self, context):
        """ Context to adapt """
        self.context = context
    
    @property
    def tags_storage(self):
        """ Acts as a storage.
        """
        try:
            return self.context.__tags_storage__
        except AttributeError:
            self.context.__tags_storage__ = OOBTree()
            return self.context.__tags_storage__
    
    def add(self, tag, userid):
        if not isinstance(tag, basestring):
            raise TypeError('tag must be a string. Was: %s' % tag)
        if not TAG_PATTERN.match(tag):
            raise ValueError("'tag' doesn't conform to tag standard: %s" % _TAG_STRING)
        if tag not in self.tags_storage:
            self.tags_storage[tag] = OOSet()

        if userid not in self.tags_storage[tag]:
            self.tags_storage[tag].add(userid)
            if tag == 'like':
                _notify(self.context)

    def userids_for_tag(self, tag):
        return tuple(self.tags_storage.get(tag, ()))

    def remove(self, tag, userid):
        if userid in self.tags_storage.get(tag, ()):
            self.tags_storage[tag].remove(userid)
            if tag == 'like':
                _notify(self.context)

def _notify(context):
    """ Send notification for Like tag. This might change later since
        the index is for a specific tag rather than a general solution.
    """
    objectEventNotify(ObjectUpdatedEvent(context, changed=('like_userids',)))


def includeme(config):
    """ Include UserTags adapter in registry.
        Call this by running config.include('voteit.core.models.user_tags')
    """
    config.registry.registerAdapter(UserTags, (IBaseContent,), IUserTags)
