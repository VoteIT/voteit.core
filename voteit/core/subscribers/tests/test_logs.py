from unittest import TestCase

from pyramid import testing
from repoze.folder.events import ObjectAddedEvent
from zope.component.event import objectEventNotify

from voteit.core.events import ObjectUpdatedEvent
from voteit.core.models.interfaces import ILogHandler
from voteit.core.testing_helpers import register_workflows
from voteit.core.testing_helpers import bootstrap_and_fixture


class LogsTests(TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m'] = Meeting()
        #Add subscribers
        self.config.scan('voteit.core.subscribers.logs')
        #Add log handler
        self.config.include('voteit.core.models.logs')
        #Add LogEntry content type
        self.config.scan('voteit.core.models.logs')
        return root

    @property
    def _base_content(self):
        from voteit.core.models.base_content import BaseContent
        return BaseContent

    def test_content_added(self):
        root = self._fixture()
        meeting = root['m']
        meeting['hello'] = self._base_content()

        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.assertEqual(len(adapter.log_storage), 1)
        self.assertEqual(adapter.log_storage[0].tags, ('added',))
        
    def test_content_removed(self):
        root = self._fixture()
        meeting = root['m']
        meeting['hello'] = self._base_content()
        del meeting['hello']
        
        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.assertEqual(len(adapter.log_storage), 2)
        self.assertEqual(adapter.log_storage[1].tags, ('removed',))
        
    def test_wf_state_change(self):
        register_workflows(self.config)
        root = self._fixture()
        meeting = root['m']
        
        meeting.set_workflow_state(self.request, 'upcoming')

        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.assertEqual(len(adapter.log_storage), 1)
        self.assertEqual(adapter.log_storage[0].tags, ('workflow',))
        
    def test_content_updated(self):
        root = self._fixture()
        meeting = root['m']

        objectEventNotify(ObjectUpdatedEvent(meeting))

        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.assertEqual(len(adapter.log_storage), 1)
        self.assertEqual(adapter.log_storage[0].tags, ('updated',))

    def test_content_not_updated_when_only_read(self):
        root = self._fixture()
        meeting = root['m']

        objectEventNotify(ObjectUpdatedEvent(meeting, indexes=('unread',)))

        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.assertEqual(len(adapter.log_storage), 0)
