import unittest

from pyramid import testing
from zope.interface.verify import verifyObject


class AgendaTemplateTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.agenda_template import AgendaTemplate
        return AgendaTemplate()
    
    def _fill_obj(self, obj):
        from voteit.core.models.agenda_item import AgendaItem

        a1 = AgendaItem()
        a1.set_field_value('title', u'A1')
        a1.set_field_value('description', u'Agenda item 1')
        
        a2 = AgendaItem()
        a2.set_field_value('title', u'A2')
        a2.set_field_value('description', u'Agenda item 2')
        
        a3 = AgendaItem()
        a3.set_field_value('title', u'A3')
        a3.set_field_value('description', u'Agenda item 3')
        
        obj.set_field_value('agenda_items', (a1, a2, a3))

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IAgendaTemplate
        obj = self._make_obj()
        self.assertTrue(verifyObject(IAgendaTemplate, obj))
        
    def test_populate_meeting(self):
        obj = self._make_obj()
        self._fill_obj(obj)
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        
        obj.populate_meeting(meeting)
        
        self.assertEqual(len(meeting), 3)
        
        self.assertEqual(meeting.values()[0].get_field_value('title'), 'A1')