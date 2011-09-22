from zope.interface import implements
from BTrees.OOBTree import OOSet

from voteit.core.security import find_authorized_userids
from voteit.core.security import VIEW
from voteit.core.models.interfaces import IUnreadAware


class UnreadAware(object):
    """ Mixin class that provides unread functionality to an object.
        This means that all users that have access to an object of this kind
        will have it marked as unread when it is added, or any other action that
        seems appropriate. (This is normally done with subscribers)
    """
    implements(IUnreadAware)
    
    @property
    def unread_storage(self):
        """ Acts as a storage. Contains all userids of users who haven't read this context.
        """
        if not hasattr(self, '__unread_storage__'):
            self.__unread_storage__ = OOSet()
        return self.__unread_storage__
    
    def mark_all_unread(self):
        """ Set as unread for all users with view permission.
        """
        userids_with_view_perm = find_authorized_userids(self, (VIEW, ))
        self.unread_storage.update(userids_with_view_perm)
    
    def mark_as_read(self, userid):
        """ Remove a userid from unread_userids if it exist in there.
            Just a convenience method in case the storage of userids change.
        """
        if userid in self.get_unread_userids():
            self.unread_storage.remove(userid)

    def get_unread_userids(self):
        return frozenset(self.unread_storage.keys())
    