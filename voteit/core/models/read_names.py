from arche.interfaces import IObjectWillBeRemovedEvent
from pyramid.decorator import reify
from pyramid.interfaces import IRequest
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface
from pyramid.traversal import resource_path
from six import string_types
from zope.component import adapter
from zope.interface import implementer
from repoze.catalog.query import Any
from repoze.catalog.query import Eq

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IReadNames
from voteit.core.models.interfaces import IReadNamesCounter


@implementer(IReadNames)
@adapter(IAgendaItem, IRequest)
class ReadNames(object):
    """ Keep track of read items."""
    track_types = ('Proposal', 'DiscussionPost')

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @reify
    def path_query(self):
        return Eq('path', resource_path(self.context))

    @reify
    def meeting(self):
        meeting = getattr(self.request, 'meeting', None)
        if not meeting: #pragma: no coverage
            meeting = find_interface(self.context, IMeeting)
        return meeting

    @reify
    def rnc(self):
        return self.request.registry.getMultiAdapter([self.meeting, self.request], IReadNamesCounter)

    def __getitem__(self, userid):
        return self.request.redis_conn.smembers(self.get_key(userid))

    def get(self, userid, default=None):
        try:
            return self[userid]
        except KeyError:
            return default

    def get_users_index_key(self):
        return "%s:ur:uindex" % self.context.uid

    def get_key(self, userid):
        return "%s:ur:%s" % (self.context.uid, userid)

    def get_len_key(self, type_name, userid):
        assert type_name in self.track_types
        return "%s:%s:urc:%s" % (self.context.uid, type_name, userid)

    def mark_read(self, names, userid):
        if isinstance(names, string_types):
            names = [names]
        #The ones that aren't stored already
        # FIXME: optimize this if needed!
        key = self.get_key(userid)
        new_names = set()
        with self.request.redis_conn.pipeline() as pipe:
            if pipe.exists(names) != len(names):
                for name in names:
                    if pipe.sadd(key, name):
                        new_names.add(name)
            if new_names:
                pipe.sadd(self.get_users_index_key(), userid)
            pipe.execute()
        if new_names:
            self.update_cached_len(userid)
        return new_names

    def update_cached_len(self, userid):
        read_names = self.request.redis_conn.smembers(self.get_key(userid))
        base_query = self.path_query & Any('__name__', read_names)
        for type_name in self.track_types:
            res = self.request.root.catalog.query(base_query & Eq('type_name', type_name))[0]
            old_len = self.get_read_type(type_name, userid)
            self.request.redis_conn.set(self.get_len_key(type_name, userid), res.total)
            changed = res.total - old_len
            self.rnc.change(type_name, changed, userid)

    def get_unread(self, names, userid):
        read_names = self.request.redis_conn.smembers(self.get_key(userid))
        return set(names) - set(read_names)

    def get_read_type(self, type_name, userid):
        try:
            return int(self.request.redis_conn.get(self.get_len_key(type_name, userid)))
        except (ValueError, TypeError):
            return 0

    def get_type_count(self, type_name):
        query = self.path_query & Eq('type_name', type_name)
        res = self.request.root.catalog.query(query)[0]
        return res.total

    def tracked_removed(self, context):
        # This may be quite slow and should perhaps be offloaded to a worker.
        # However, it will only impact delete operations, which only moderators can do.
        assert context.type_name in self.track_types
        name = context.__name__
        userids = self.request.redis_conn.smembers(self.get_users_index_key())
        for userid in userids:
            self.request.redis_conn.srem(self.get_key(userid), name)
            # FIXME: This should be optimized
            self.update_cached_len(userid)

    def __bool__(self):
        return True
    __nonzero__ = __bool__


@implementer(IReadNamesCounter)
@adapter(IMeeting, IRequest)
class ReadNamesCounter(object):
    """ Keep track of current count of read items for the meeting. """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_key(self, type_name, userid):
        return "%s:%s:rnc:%s" % (self.context.uid, type_name, userid)

    def change(self, type_name, num, userid):
        if num != 0:
            curr = self.get_read_count(type_name, userid)
            self.request.redis_conn.set(self.get_key(type_name, userid), curr + num)

    def get_read_count(self, type_name, userid):
        try:
            return int(self.request.redis_conn.get(self.get_key(type_name, userid)))
        except (ValueError, TypeError):
            return 0

    def __bool__(self):
        return True
    __nonzero__ = __bool__


def remove_context_from_read(context, event):
    ai = find_interface(context, IAgendaItem)
    request = getattr(event, 'request', get_current_request())
    if ai:
        read_names = request.get_read_names(ai)
        read_names.tracked_removed(context)


def get_read_names(request, context):
    assert IAgendaItem.providedBy(context)
    return request.registry.queryMultiAdapter([context, request], IReadNames)


def get_read_count(request, meeting, type_name, userid=None):
    if userid is None:
        userid = request.authenticated_userid
    assert isinstance(userid, string_types)
    assert IMeeting.providedBy(meeting)
    rnc = request.registry.getMultiAdapter([meeting, request], IReadNamesCounter)
    return rnc.get_read_count(type_name, userid)


def includeme(config):
    #When something is moved, the read status will be deleted.
    #I don't think that's a problem /robinharms
    config.registry.registerAdapter(ReadNames)
    config.registry.registerAdapter(ReadNamesCounter)
    config.add_request_method(get_read_names)
    config.add_request_method(get_read_count)
    config.add_subscriber(remove_context_from_read, [IProposal, IObjectWillBeRemovedEvent])
    config.add_subscriber(remove_context_from_read, [IDiscussionPost, IObjectWillBeRemovedEvent])
