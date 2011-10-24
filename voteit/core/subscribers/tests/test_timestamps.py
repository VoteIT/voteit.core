from unittest import TestCase
from datetime import datetime

from pyramid import testing


class TimestampsTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.scan('voteit.core.subscribers.timestamps')
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    def _make_ai(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()
        
    def _make_meeting(self):
        from voteit.core.models.meeting import Meeting
        return Meeting()

    def test_ai(self):
        request = testing.DummyRequest()
        
        obj = self._make_ai()
        
        obj.set_workflow_state(request, 'upcoming')
        
        obj.set_workflow_state(request, 'ongoing')
        self.assertFalse(isinstance(obj.end_time, datetime))
        
        obj.set_workflow_state(request ,'closed')
        self.assertTrue(isinstance(obj.end_time, datetime))
        
        obj.set_workflow_state(request, 'ongoing')
        self.assertFalse(isinstance(obj.end_time, datetime))
        
    def test_meeting(self):
        request = testing.DummyRequest()
        
        obj = self._make_meeting()
        
        obj.set_workflow_state(request, 'ongoing')
        self.assertFalse(isinstance(obj.end_time, datetime))
        
        obj.set_workflow_state(request ,'closed')
        self.assertTrue(isinstance(obj.end_time, datetime))
        
        obj.set_workflow_state(request, 'ongoing')
        self.assertFalse(isinstance(obj.end_time, datetime))
