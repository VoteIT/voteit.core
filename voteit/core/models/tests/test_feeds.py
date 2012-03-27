import unittest
from datetime import datetime

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.component.interfaces import IFactory
from zope.component import createObject

from voteit.core.models.interfaces import IFeedHandler


class FeedHandlerTests(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)

    def tearDown(self):
        testing.tearDown()

    def _make_adapted_obj(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.feeds import FeedHandler
        context = Meeting()
        return FeedHandler(context)

    def _register_feed_entry_factory(self):
        #FIXME: Detach more?
        self.config.scan('voteit.core.models.feeds')

    def test_interface(self):
        obj = self._make_adapted_obj()
        self.assertTrue(verifyObject(IFeedHandler, obj))

    def test_add(self):
        self._register_feed_entry_factory()
        obj = self._make_adapted_obj()
        obj.add('context_uid', 'message')
        
        self.assertEqual(len(obj.feed_storage), 1)
        self.assertEqual(obj.feed_storage[0].context_uid, 'context_uid')
        self.assertEqual(obj.feed_storage[0].message, 'message')

    def test_registration_on_include(self):
        self.config.include('voteit.core.models.feeds')
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        adapter = self.config.registry.queryAdapter(meeting, IFeedHandler)
        self.failUnless(IFeedHandler.providedBy(adapter))


class FeedEntryTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.feeds import FeedEntry
        return FeedEntry

    def test_interface(self):
        from voteit.core.models.interfaces import IFeedEntry
        obj = self._cut('uid', 'message')
        self.assertTrue(verifyObject(IFeedEntry, obj))

    def test_construction(self):
        obj = self._cut('uid', 'message', tags=['hello', 'world'])
        self.assertTrue(isinstance(obj.created, datetime))
        self.assertEqual(obj.context_uid, 'uid')
        self.assertEqual(obj.message, u'message')
        self.assertEqual(obj.tags, ('hello', 'world'))

    def test_factory_registered_on_scan(self):
        self.config.scan('voteit.core.models.feeds')
        
        factory = self.config.registry.queryUtility(IFactory, 'FeedEntry')
        self.failUnless(IFactory.providedBy(factory))
        obj = factory('uid', 'message')
        self.failUnless(obj)
        obj = createObject('FeedEntry', 'uid', 'message')
        self.failUnless(obj)