import re

from BTrees.OOBTree import OOSet
from zope.interface import implements
from zope.component.event import objectEventNotify

from voteit.core.models.interfaces import ITags
from voteit.core.events import ObjectUpdatedEvent


TAG_PATTERN = re.compile(r'(\A|\s|[,.;:!?])#(?P<tag>\w*[\w-]+)(\w*)', flags=re.UNICODE)

class Tags(object):
    """ Tags mixin.
        See :mod:`voteit.core.models.interfaces.ITags`.
    """
    implements(ITags)
    
    @property
    def _tags(self):
        """ Acts as a storage.
        """
        try:
            return self.__tags__
        except AttributeError:
            self.__tags__ = OOSet()
            return self.__tags__
    
    def find_tags(self, value):
        tags = set()
        for matchobj in re.finditer(TAG_PATTERN, value):
            tags.add(matchobj.group('tag').lower())
        return tags

    def add_tags(self, tags, notify = False):
        if isinstance(tags, basestring):
            tags = [x.strip() for x in tags.split()]
        for tag in tags:
            self._tags.add(tag.lower())
        if notify:
            objectEventNotify(ObjectUpdatedEvent(self, indexes=('tags',), metadata=True))

    def set_tags(self, tags, notify = False):
        self._tags.clear()
        self.add_tags(tags, notify = notify)

    def remove_tags(self, tags, notify = False):
        if isinstance(tags, basestring):
            tags = [x.strip() for x in tags.split()]
        for tag in tags:
            self._tags.remove(tag.lower())
        if notify:
            objectEventNotify(ObjectUpdatedEvent(self, indexes=('tags',), metadata=True))

#FIXME: Inetegration tests, catalog etc
