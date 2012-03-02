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
        obj.set_field_value('agenda_items', [{'description': u'Agenda Item 1', 'title': u'A1'},
                                             {'description': u'Agenda Item 2', 'title': u'A2'},
                                             {'description': u'Agenda Item 3', 'title': u'A3'},])

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