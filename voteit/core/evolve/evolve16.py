from pyramid.threadlocal import get_current_request

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting


_TYPES = ('Proposal', 'DiscussionPost')


def convert_ai(ai, users):
    unread_names_for_user = {}
    for userid in users:
        unread_names_for_user[userid] = set()
    ai_keys = set()
    #Take all users from local roles and add them as read if they don't exist here
    for obj in ai.values():
        if obj.type_name in _TYPES and hasattr(obj, '__unread_storage__'):
            #Only process ai_keys that have the __unread_storage__ attribute
            #Otherwise everything will be read.
            ai_keys.add(obj.__name__)
            for userid in obj.__unread_storage__:
                if userid in users:
                    unread_names_for_user[userid].add(obj.__name__)
            delattr(obj, '__unread_storage__')
    #Make sure all users are included. they might have read everything.
    request = get_current_request()
    rn = request.get_read_names(ai)
    for userid, unread_names in unread_names_for_user.items():
        read_names = ai_keys - unread_names
        rn.mark_read(read_names, userid)


def evolve(root):
    """ Migrate all old unread markers that were stored in the catalog.
    """
    if '__name__' not in root.catalog:
        raise KeyError("__name__ index must be in catalog before this migration."
                       "Run catalog update first.")
    #We only need to care about meetings
    for m in root.values():
        if not IMeeting.providedBy(m):
            continue
        users = set(root.local_roles) | set(m.local_roles)
        for ai in m.values():
            if not IAgendaItem.providedBy(ai):
                continue
            convert_ai(ai, users)
        print "Processed '%s' for %s users" % (m.__name__, len(users))
