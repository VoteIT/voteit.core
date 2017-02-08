from arche.interfaces import ICataloger
from arche.utils import find_all_db_objects

from voteit.core.models.interfaces import IUserUnread


def evolve(root):
    """ Migrate all old unread markers
    """
    if 'unread' in root.catalog:
        del root.catalog['unread']
    users = root['users']
    for obj in find_all_db_objects(root):
        if hasattr(obj, '__unread_storage__') and obj.type_name in ('Proposal', 'DiscussionPost'):
            for userid in obj.__unread_storage__:
                if userid in users:
                    unread = IUserUnread(users[userid])
                    unread.add(obj)
            delattr(obj, '__unread_storage__')
            ICataloger(obj).index_object()
