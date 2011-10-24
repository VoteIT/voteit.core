from unittest import TestCase

from pyramid import testing
from repoze.folder.events import ObjectAddedEvent
from zope.component.event import objectEventNotify

from voteit.core.events import ObjectUpdatedEvent
from voteit.core.models.interfaces import ILogHandler
from voteit.core.testing_helpers import register_workflows


class LogsTests(TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()
        
    def _fixture(self):
        return bootstrap_and_fixture(self.config)

    @property
    def _make_obj(self):
        from voteit.core.models.meeting import Meeting
        return Meeting

    def test_content_added(self):
        #Add subscribers
        self.config.scan('voteit.core.subscribers.logs')
        #Add log handler
        self.config.include('voteit.core.models.logs')
        #Add LogEntry content type
        self.config.scan('voteit.core.models.logs')

        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting

        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.assertEqual(len(adapter.log_storage), 1)
        self.assertEqual(adapter.log_storage[0].tags, ('added',))
        
        
    def test_content_removed(self):
        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting

        #Add subscribers
        self.config.scan('voteit.core.subscribers.logs')
        #Add log handler
        self.config.include('voteit.core.models.logs')
        #Add LogEntry content type
        self.config.scan('voteit.core.models.logs')
        
        del root['meeting']

        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.assertEqual(len(adapter.log_storage), 1)
        self.assertEqual(adapter.log_storage[0].tags, ('removed',))
        
    def test_wf_state_change(self):
        register_workflows(self.config)
    
        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting

        #Add subscribers
        self.config.scan('voteit.core.subscribers.logs')
        #Add log handler
        self.config.include('voteit.core.models.logs')
        #Add LogEntry content type
        self.config.scan('voteit.core.models.logs')
        
        meeting.set_workflow_state(self.request, 'upcoming')

        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.assertEqual(len(adapter.log_storage), 1)
        self.assertEqual(adapter.log_storage[0].tags, ('workflow',))
        
    def test_content_updated(self):
        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting

        #Add subscribers
        self.config.scan('voteit.core.subscribers.logs')
        #Add log handler
        self.config.include('voteit.core.models.logs')
        #Add LogEntry content type
        self.config.scan('voteit.core.models.logs')

        objectEventNotify(ObjectUpdatedEvent(meeting, None, 'dummy'))

        adapter = self.config.registry.queryAdapter(meeting, ILogHandler)
        self.assertEqual(len(adapter.log_storage), 1)
        self.assertEqual(adapter.log_storage[0].tags, ('updated',))
