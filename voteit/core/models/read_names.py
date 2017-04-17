from BTrees.Length import Length
from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import Set
from arche.compat import IterableUserDict
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
from zope.interface.interfaces import ComponentLookupError


@implementer(IReadNames)
@adapter(IAgendaItem, IRequest)
class ReadNames(IterableUserDict):
    """ Keep track of read items. The base ZODB-version isn't great for
        large live meetings.

        It's a good idea to replace it with a redis-based version
        with non-expiring keys for those occasions.
        """
    track_types = ('Proposal', 'DiscussionPost')

    def __init__(self, context, request):
        self.context = context
        self.request = request
        try:
            self.data = context._read_names
        except AttributeError:
            self.data = context._read_names = OOBTree()

    @reify
    def path_query(self):
        return Eq('path', resource_path(self.context))

    @reify
    def meeting(self):
        meeting = getattr(self.request, 'meeting', None)
        if not meeting: #pragma: no coverage
            meeting = find_interface(self.context, IMeeting)
        return meeting

    def __setitem__(self, key, value):
        self.data[key] = Set(value)

    def mark_read(self, names, userid):
        if isinstance(names, string_types):
            names = [names]
        #The ones that aren't stored already
        names = self.get_unread(names, userid)
        if names:
            if userid in self:
                self[userid].update(names)
            else:
                self[userid] = names
            self.update_chached_len(names, userid)
            return names
        return set() #pragma: no coverage

    def update_chached_len(self, names, userid):
        try:
            rnc = self.request.registry.getMultiAdapter([self.meeting, self.request], IReadNamesCounter)
        except ComponentLookupError: #For simpler tests
            rnc = ReadNamesCounter(self.meeting, self.request)
        base_query = self.path_query & Any('__name__', names)
        for type_name in self.track_types:
            res = self.request.root.catalog.query(base_query & Eq('type_name', type_name))[0]
            rnc.change(type_name, res.total, userid)

    def get_unread(self, names, userid):
        return set(names) - set(self.get(userid, ()))

    def get_read_type(self, type_name, userid):
        read_names = self.get(userid, ())
        if read_names:
            query = self.path_query & Eq('type_name', type_name) & Any('__name__', read_names)
            res = self.request.root.catalog.query(query)[0]
            return res.total
        return 0

    def get_type_count(self, type_name):
        query = self.path_query & Eq('type_name', type_name)
        res = self.request.root.catalog.query(query)[0]
        return res.total

    def tracked_removed(self, context):
        assert context.type_name in self.track_types
        rnc = self.request.registry.getMultiAdapter([self.meeting, self.request], IReadNamesCounter)
        name = context.__name__
        for (userid, curr) in self.items():
            if name in curr:
                curr.remove(name)
                rnc.change(context.type_name, -1, userid)

    def __bool__(self):
        return True
    __nonzero__ = __bool__


@implementer(IReadNamesCounter)
@adapter(IMeeting, IRequest)
class ReadNamesCounter(IterableUserDict):
    """ Keep track of current count of read items """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        try:
            self.data = context._read_names_counter
        except AttributeError:
            self.data = context._read_names_counter = OOBTree()

    def change(self, type_name, num, userid):
        if userid not in self:
            self.data[userid] = OOBTree()
        storage = self.data[userid]
        if type_name not in storage:
            storage[type_name] = Length()
        storage[type_name].change(num)

    def get_read_count(self, type_name, userid):
        if userid in self:
            storage = self[userid]
            if type_name in storage:
                return storage[type_name]()
        return 0

    def __setitem__(self, key, value):
        raise Exception("Shouldn't be accessed directly, use change() method")

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
