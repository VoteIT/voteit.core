from pyramid.threadlocal import get_current_request

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting


def evolve(root):
    """ Migrate unread to redis
    """
    try:
        from fakeredis import FakeStrictRedis
        maybe_fr = True
    except ImportError:
        maybe_fr = False
    request = get_current_request()
    if maybe_fr:
        if isinstance(request.redis_conn, FakeStrictRedis):
            raise Exception("Your redis connection is a FakeRedis instance. "
                            "All migrated data would be thrown away! "
                            "Please set voteit.redis_url in your paster.ini file.")
    for meeting in [x for x in root.values() if IMeeting.providedBy(x)]:
        if hasattr(meeting, '_read_names_counter'):
            delattr(meeting, '_read_names_counter')
        for ai in [x for x in meeting.values() if IAgendaItem.providedBy(x)]:
            if not hasattr(ai, '_read_names'):
                continue
            read_names = request.get_read_names(ai)
            for (userid, names) in ai._read_names.items():
                read_names.mark_read(names, userid)
