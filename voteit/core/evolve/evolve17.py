from arche.interfaces import IUser
from pyramid.threadlocal import get_current_request

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting


def extract_userinfo(user, found):
    """ append found dict. Structure as:
        {<ai uid>: {<userid>: <unread_uids>}}
    """
    for ai_uid, type_storages in user._unread.items():
        unread_uids = set()
        for uids in type_storages.values():
            unread_uids.update(uids)
        if ai_uid not in found:
            found[ai_uid] = {}
        found[ai_uid].update({user.userid: unread_uids})
    delattr(user, '_unread')


def find_ais(root, found):
    for m in root.values():
        if not IMeeting.providedBy(m):
            continue
        print "Processing: /%s" % m.__name__
        for ai in m.values():
            if not IAgendaItem.providedBy(ai) or ai.uid not in found:
                continue
            mark_read(ai, found.pop(ai.uid))
            if not found:
                return


def mark_read(ai, unreads):
    uid_map = {}
    for obj in ai.values():
        uid_map[obj.uid] = obj.__name__
    ai_keys = set(uid_map)
    request = get_current_request()
    rn = request.get_read_names(ai)
    for userid, unread_uids in unreads.items():
        unread_names = set()
        for x in unread_uids:
            if x in uid_map:
                unread_names.add(uid_map[x])
        read_names = ai_keys - unread_names
        rn.mark_read(read_names, userid)


def evolve(root):
    """ Evolve to read markers instead of unread
    """
    if '__name__' not in root.catalog:
        raise KeyError("__name__ index must be in catalog before this migration."
                       "Run catalog update first.")
    print "Walking through users..."
    found = {}
    for user in root['users'].values():
        if not IUser.providedBy(user):
            continue
        #No need to migrate
        if hasattr(user, '_unread_counter'):
            delattr(user, '_unread_counter')
        if hasattr(user, '_unread'):
            extract_userinfo(user, found)
    print "Walking through ais..."
    find_ais(root, found)
