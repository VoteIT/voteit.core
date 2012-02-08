import unittest

from pyramid import testing
from zope.component.event import objectEventNotify

from voteit.core.events import ObjectUpdatedEvent
from voteit.core.testing_helpers import register_workflows


class PollTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.scan('voteit.core.subscribers.agenda_item')

    def tearDown(self):
        testing.tearDown()

    def test_change_states_proposals(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)

        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        meeting = Meeting()
        
        ai = AgendaItem()
        meeting['a1'] = ai
        
        ai = AgendaItem()
        meeting['a2'] = ai
        
        self.assertEqual(meeting['a1'].get_field_value('order'), 0)
        self.assertEqual(meeting['a2'].get_field_value('order'), 1)
