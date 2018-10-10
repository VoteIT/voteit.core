import unittest

from arche.testing import barebone_fixture
from fakeredis import FakeRedis
from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from pyramid.request import apply_request_extensions

from voteit.core.models.interfaces import IReadNames
from voteit.core.models.interfaces import IReadNamesCounter


class ReadNamesTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing')

    def tearDown(self):
        testing.tearDown()
        FakeRedis().flushall()

    @property
    def _cut(self):
        from voteit.core.models.read_names import ReadNames
        return ReadNames

    def test_verify_class(self):
        self.failUnless(verifyClass(IReadNames, self._cut))

    def test_verify_obj(self):
        obj = self._cut(testing.DummyModel(), testing.DummyRequest())
        self.failUnless(verifyObject(IReadNames, obj))

    def _fixture(self):
        self.config.include('arche.testing.catalog')
        self.config.include('voteit.core.models.catalog')
        self.config.include('voteit.core.testing_helpers.register_workflows')
        self.config.include('voteit.core.helpers')
        self.config.include('voteit.core.models.read_names')
        from voteit.core.models.meeting import Meeting
        request = testing.DummyRequest()
        root = barebone_fixture(self.config)
        request.root = root
        apply_request_extensions(request)
        self.config.begin(request)
        root['m'] = request.meeting = Meeting()
        return root['m'], request

    def test_emtpy_instance_truthy(self):
        self.assertTrue(self._cut(testing.DummyModel(), None))

    def test_mark_read(self):
        meeting, request = self._fixture()
        obj = self._cut(meeting, request)
        obj.mark_read(['a', 'b'], 'hanna')
        obj.mark_read(['a', 'c'], 'hanna')
        self.assertEqual(set(obj['hanna']), set(['a', 'b', 'c']))

    def test_get_unread(self):
        meeting, request = self._fixture()
        obj = self._cut(meeting, request)
        obj.mark_read(['a', 'b'], 'hanna')
        obj.mark_read(['a', 'c'], 'hanna')
        self.assertFalse(obj.get_unread([], 'frej'))
        self.assertEqual(obj.get_unread(['a', 'b'], 'frej'), set(['a', 'b']))
        self.assertEqual(obj.get_unread(['a', 'b', 'c', 'd', 'e'], 'hanna'),
                         set(['d', 'e']))

    def test_get_read_type(self):
        meeting, request = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        meeting['ai'] = ai = AgendaItem()
        obj = self._cut(ai, request)
        self.assertEqual(obj.get_read_type('Proposal', 'anders'), 0)
        ai['p1'] = Proposal()
        self.assertEqual(obj.get_read_type('Proposal', 'anders'), 0)
        obj.mark_read('p1', 'anders')
        self.assertEqual(obj.get_read_type('Proposal', 'anders'), 1)

    def test_get_type_count(self):
        meeting, request = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        meeting['ai'] = ai = AgendaItem()
        obj = self._cut(ai, request)
        ai['p1'] = Proposal()
        self.assertEqual(obj.get_type_count('Proposal'), 1)
        ai['p2'] = Proposal()
        self.assertEqual(obj.get_type_count('Proposal'), 2)

    def test_integration(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        meeting, request = self._fixture()
        self.config.include('voteit.core.models.read_names')
        meeting['ai'] = ai = AgendaItem()
        ai['a'] = Proposal()
        ai['b'] = Proposal()
        obj = self._cut(ai, request)
        obj.mark_read(['a', 'b'], 'sanna')
        self.assertEqual(obj.get_read_type('Proposal', 'sanna'), 2)
        del ai['a']
        self.assertEqual(obj.get_read_type('Proposal', 'sanna'), 1)
        self.assertEqual(set(obj['sanna']), set(['b']))


class ReadNamesCounterTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing')

    def tearDown(self):
        testing.tearDown()
        FakeRedis().flushall()

    @property
    def _cut(self):
        from voteit.core.models.read_names import ReadNamesCounter
        return ReadNamesCounter

    def test_verify_class(self):
        self.failUnless(verifyClass(IReadNamesCounter, self._cut))

    def test_verify_obj(self):
        obj = self._cut(testing.DummyModel(), testing.DummyRequest())
        self.failUnless(verifyObject(IReadNamesCounter, obj))

    def test_emtpy_instance_truthy(self):
        self.assertTrue(self._cut(testing.DummyModel(), None))

    def test_change(self):
        request = testing.DummyRequest()
        self.config.include('voteit.core.helpers')
        apply_request_extensions(request)
        obj = self._cut(testing.DummyModel(uid='hi'), request)
        obj.change('Dummy', 1, 'robin')
        self.assertEqual(obj.get_read_count('Dummy', 'robin'), 1)
        obj.change('Dummy', -2, 'robin')
        self.assertEqual(obj.get_read_count('Dummy', 'robin'), -1)
        obj.change('Dummy', +3, 'robin')
        self.assertEqual(obj.get_read_count('Dummy', 'robin'), 2)

    def test_get_read_count(self):
        request = testing.DummyRequest()
        self.config.include('voteit.core.helpers')
        apply_request_extensions(request)
        obj = self._cut(testing.DummyModel(uid='hi'), request)
        obj.change('Dummy', 1, 'robin')
        self.assertEqual(obj.get_read_count('Dummy', 'robin'), 1)
        obj.change('Dummy', -2, 'robin')
        self.assertEqual(obj.get_read_count('Dummy', 'robin'), -1)
        obj.change('Dummy', +3, 'robin')
        self.assertEqual(obj.get_read_count('Dummy', 'robin'), 2)

    def test_integration(self):
        from voteit.core.models.meeting import Meeting
        self.config.include('arche.testing.catalog')
        self.config.include('voteit.core.models.catalog')
        self.config.include('voteit.core.testing_helpers.register_workflows')
        self.config.include('voteit.core.helpers')
        self.config.include('voteit.core.models.read_names')
        request = testing.DummyRequest()
        root = barebone_fixture(self.config)
        request.root = root
        apply_request_extensions(request)
        self.config.begin(request)
        root['m'] = meeting = Meeting()
        self.assertEqual(request.get_read_count(meeting, 'Proposal', 'frej'), 0)
        obj = self._cut(meeting, request)
        obj.change('Dummy', 3, 'frej')
        self.assertEqual(obj.get_read_count('Dummy', 'frej'), 3)
        self.assertEqual(request.get_read_count(meeting, 'Dummy', 'frej'), 3)

    def test_integration_read_count(self):
        from voteit.core.models.meeting import Meeting
        self.config.include('arche.testing.catalog')
        self.config.include('voteit.core.models.catalog')
        self.config.include('voteit.core.testing_helpers.register_workflows')
        self.config.include('voteit.core.helpers')
        self.config.include('voteit.core.models.read_names')
        request = testing.DummyRequest()
        root = barebone_fixture(self.config)
        request.root = root
        apply_request_extensions(request)
        self.config.begin(request)
        root['m'] = meeting = Meeting()
        self.assertEqual(request.get_read_count(meeting, 'Proposal', 'frej'), 0)
        obj = self._cut(meeting, request)
        obj.change('Dummy', 3, 'frej')
        self.assertEqual(obj.get_read_count('Dummy', 'frej'), 3)
        self.assertEqual(request.get_read_count(meeting, 'Dummy', 'frej'), 3)
