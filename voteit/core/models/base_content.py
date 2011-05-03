
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
