import re

from BTrees.OOBTree import OOSet
from zope.interface import implements
from zope.component.event import objectEventNotify

from voteit.core.models.interfaces import ITags
from voteit.core.events import ObjectUpdatedEvent


TAG_PATTERN = re.compile(r'(\A|\s|[,.;:!?])#(?P<tag>\w*[a-zA-Z0-9-_]+)(\w*)')

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
    
    def _find_tags(self, value):
        for matchobj in re.finditer(TAG_PATTERN, value):
            tag = matchobj.group('tag')
            self._tags.add(tag.lower())
            
    def add_tag(self, tag):
        self._tags.add(tag.lower())
        objectEventNotify(ObjectUpdatedEvent(self, indexes=('tags',), metadata=True))
        
    def add_tags(self, tags):
        for tag in tags.split():
            self._tags.add(tag.lower())
        objectEventNotify(ObjectUpdatedEvent(self, indexes=('tags',), metadata=True))
        
    def remove_tag(self, tag):
        self._tags.remove(tag.lower())
        objectEventNotify(ObjectUpdatedEvent(self, indexes=('tags',), metadata=True))