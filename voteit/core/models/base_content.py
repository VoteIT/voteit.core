from uuid import uuid4

from repoze.folder import Folder
from zope.interface import implements
from BTrees.OOBTree import OOBTree

from pyramid.security import Allow, Everyone, Authenticated, Deny,\
    ALL_PERMISSIONS

from voteit.core.models.interfaces import IBaseContent


class BaseContent(Folder):
    __doc__ = IBaseContent.__doc__
    implements(IBaseContent)
    
    #__acl__ = [(Allow, Authenticated, View),
    #           (Allow, Authenticated, Edit),
    #           (Allow, Authenticated, Add),
    #           (Deny, Everyone, ALL_PERMISSIONS),]

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
    def _set_uid(self, value):
        self.__UID__ = value
        
    def _get_uid(self):
        return getattr(self, '__UID__', None)
    
    uid = property(_get_uid, _set_uid)

    #title
    def _set_title(self, value):
        self.set_field_value('title', value)
    
    def _get_title(self):
        return self.get_field_value('title')

    title = property(_get_title, _set_title)
