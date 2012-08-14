import re

from BTrees.OOBTree import OOSet
from zope.interface import implements
from zope.component.event import objectEventNotify

from voteit.core.models.interfaces import ITags
from voteit.core.models.interfaces import IBaseContent
from voteit.core.events import ObjectUpdatedEvent


TAG_PATTERN = re.compile(r'\B#(?P<tag>\w*[a-zA-Z]+)\w*')

class Tags(object):
    """ Tags mixin.
        See :mod:`voteit.core.models.interfaces.ITags`.
    """
    implements(ITags)
    
    @property
    def tags(self):
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
            self.tags.add(tag)
            objectEventNotify(ObjectUpdatedEvent(self, indexes=('tags',), metadata=True))