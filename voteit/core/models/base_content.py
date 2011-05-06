from uuid import uuid4

from repoze.folder import Folder
from zope.interface import implements
from BTrees.OOBTree import OOBTree

from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.security_aware import SecurityAware



class BaseContent(Folder, SecurityAware):
    __doc__ = IBaseContent.__doc__
    implements(IBaseContent)
    add_permission = None
    content_type = None
    omit_fields_on_edit = ()
    allowed_contexts = ()

    def __init__(self):
        self.uid = str(uuid4())
        super(BaseContent, self).__init__()

    @property
    def _storage(self):
        storage = getattr(self, '__storage__', None)
        if storage is None:
            storage = self.__storage__ =  OOBTree()
        return storage

    def set_field_value(self, key, value):
        """ Store value in 'key' in annotations. """
        self._storage[key] = value

    def get_field_value(self, key, default=None):
        """ Get value. Return default if it doesn't exist. """
        return self._storage.get(key, default)

    #uid
    def _get_uid(self):
        return getattr(self, '__UID__', None)
    
    def _set_uid(self, value):
        self.__UID__ = value
        
    uid = property(_get_uid, _set_uid)

    #title
    def _get_title(self):
        return self.get_field_value('title')
    
    def _set_title(self, value):
        self.set_field_value('title', value)

    title = property(_get_title, _set_title)

    def _get_description(self):
        return self.get_field_value('description')
    
    def _set_description(self, value):
        self.set_field_value('description', value)

    description = property(_get_description, _set_description)

    #creators
    def _get_creators(self):
        return getattr(self, '__creators__', ())

    def _set_creators(self, value):
        self.__creators__ = tuple(value)
    
    creators = property(_get_creators, _set_creators)
    