import re

from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOSet
from zope.interface import implements
from zope.component.event import objectEventNotify

from voteit.core.models.interfaces import IUserTags
from voteit.core.models.interfaces import IBaseContent
from voteit.core.events import ObjectUpdatedEvent


TAG_PATTERN = re.compile(r'^[a-zA-Z\_\-]{3,15}$')


class UserTags(object):
    __doc__ = IUserTags.__doc__
    implements(IUserTags)
    
    def __init__(self, context):
        """ Context to adapt """
        self.context = context
    
    @property
    def tags_storage(self):
        """ Acts as a storage.
        """
        if not hasattr(self.context, '__tags_storage__'):
            self.context.__tags_storage__ = OOBTree()
        return self.context.__tags_storage__
    
    def add(self, tag, userid):
        if not isinstance(tag, basestring):
            raise TypeError('tag must be a string. Was: %s' % tag)
        if not TAG_PATTERN.match(tag):
            raise ValueError("'tag' doesn't conform to tag standard: '^[a-zA-Z\_\-]{3,15}$'")
        if tag not in self.tags_storage:
            self.tags_storage[tag] = OOSet()

        if userid not in self.tags_storage[tag]:
            self.tags_storage[tag].add(userid)
            if tag == 'like':
                self._notify()

    def userids_for_tag(self, tag):
        return tuple(self.tags_storage.get(tag, ()))

    def remove(self, tag, userid):
        if userid in self.tags_storage.get(tag, ()):
            self.tags_storage[tag].remove(userid)
            if tag == 'like':
                self._notify()
    
    def _notify(self):
        objectEventNotify(ObjectUpdatedEvent(self.context, indexes=('like_userids',), metadata=True))


def includeme(config):
    """ Include UserTags adapter in registry.
        Call this by running config.include('voteit.core.models.user_tags')
    """
    config.registry.registerAdapter(UserTags, (IBaseContent,), IUserTags)
