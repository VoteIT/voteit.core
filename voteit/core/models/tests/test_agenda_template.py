import unittest

from pyramid import testing
from pyramid.security import principals_allowed_by_permission
from zope.interface.verify import verifyObject

from voteit.core import security
from voteit.core.testing_helpers import register_security_policies


admin = set([security.ROLE_ADMIN])
owner = set([security.ROLE_OWNER])


class AgendaTemplateTests(unittest.TestCase):
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
        self.config.scan('voteit.core.models.agenda_item')

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


class AgendaTemplatePermissionTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        register_security_policies(self.config)
        
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.agenda_template import AgendaTemplate
        return AgendaTemplate

    def test_view(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.VIEW), admin | owner)

    def test_edit(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.EDIT), admin | owner)

    def test_delete(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.DELETE), admin | owner)

    def test_manage_server(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.MANAGE_SERVER), admin)
