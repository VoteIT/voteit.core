import unittest
from datetime import datetime

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.component.interfaces import IFactory
from zope.component import createObject

from voteit.core.models.interfaces import ILogHandler


class LogHandlerTests(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)

    def tearDown(self):
        testing.tearDown()

    def _make_adapted_obj(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.logs import LogHandler
        context = Meeting()
        return LogHandler(context)

    def _register_log_entry_factory(self):
        from voteit.core.models.logs import LogEntry
        from voteit.core.app import register_factory
        register_factory(self.config, LogEntry, 'LogEntry')

    def test_interface(self):
        obj = self._make_adapted_obj()
        self.assertTrue(verifyObject(ILogHandler, obj))

    def test_add(self):
        self._register_log_entry_factory()
        obj = self._make_adapted_obj()
        obj.add('context_uid', 'message')
        
        self.assertEqual(len(obj.log_storage), 1)
        self.assertEqual(obj.log_storage[0].context_uid, 'context_uid')
        self.assertEqual(obj.log_storage[0].message, 'message')

    def test_registration_on_include(self):
        self.config.include('voteit.core.models.logs')
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.failUnless(ILogHandler.providedBy(adapter))

    def test_meeting_added_subscriber_adds_to_log(self):
        #Add subscribers
        self.config.scan('voteit.core.subscribers.logs')
        #Add log handler
        self.config.include('voteit.core.models.logs')

        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting

        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.assertEqual(len(adapter.log_storage), 1)
        self.assertEqual(adapter.log_storage[0].tags, ('added',))

#FIXME: Test removed, updated and workflow state changed!


class LogEntryTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.logs import LogEntry
        return LogEntry

    def test_interface(self):
        from voteit.core.models.interfaces import ILogEntry
        obj = self._cut('uid', 'message')
        self.assertTrue(verifyObject(ILogEntry, obj))

    def test_construction(self):
        obj = self._cut('uid', 'message', tags=['hello', 'world'], userid='hanna', scripted='by robot')
        self.assertTrue(isinstance(obj.created, datetime))
        self.assertEqual(obj.context_uid, 'uid')
        self.assertEqual(obj.message, u'message')
        self.assertEqual(obj.tags, ('hello', 'world'))
        self.assertEqual(obj.userid, 'hanna')
        self.assertEqual(obj.scripted, 'by robot')

    def test_factory_registered_on_include(self):
        self.config.include('voteit.core.models.logs')
        
        factory = self.config.registry.queryUtility(IFactory, 'LogEntry')
        self.failUnless(IFactory.providedBy(factory))
        obj = factory('uid', 'message')
        self.failUnless(obj)
        obj = createObject('LogEntry', 'uid', 'message')
        self.failUnless(obj)
        