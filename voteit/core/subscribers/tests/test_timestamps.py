from unittest import TestCase
from datetime import datetime

from pyramid import testing


class TimestampsTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('voteit.core.subscribers.timestamps')
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

    def test_timestamp_closed_set_for_ai(self):
        request = testing.DummyRequest()
        obj = self._make_ai()
        #Just to make sure
        self.assertEqual(obj.end_time, None)
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        obj.set_workflow_state(request ,'closed')
        self.assertTrue(isinstance(obj.end_time, datetime))

    def test_timestamp_closed_set_for_meeting(self):
        request = testing.DummyRequest()
        obj = self._make_meeting()
        #Just to make sure
        self.assertEqual(obj.end_time, None)
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        obj.set_workflow_state(request ,'closed')
        self.assertTrue(isinstance(obj.end_time, datetime))

    def test_timestamp_start_set_for_meeting(self):
        request = testing.DummyRequest()
        obj = self._make_meeting()
        #Just to make sure
        self.assertEqual(obj.start_time, None)
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        self.assertTrue(isinstance(obj.start_time, datetime))

    def test_timestamp_start_removed_on_retract(self):
        request = testing.DummyRequest()
        obj = self._make_meeting()
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        obj.set_workflow_state(request, 'upcoming')
        self.assertEqual(obj.start_time, None)

    def test_timestamp_end_removed_on_restart(self):
        request = testing.DummyRequest()
        obj = self._make_meeting()
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        obj.set_workflow_state(request ,'closed')
        obj.set_workflow_state(request, 'ongoing')
        self.assertEqual(obj.end_time, None)
