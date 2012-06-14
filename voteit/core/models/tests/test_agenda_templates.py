import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from pyramid.security import principals_allowed_by_permission

from voteit.core import security
from voteit.core.testing_helpers import register_security_policies


admin = set([security.ROLE_ADMIN])


class AgendaTemplatesTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.agenda_templates import AgendaTemplates
        return AgendaTemplates()

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IAgendaTemplates
        obj = self._make_obj()
        self.assertTrue(verifyObject(IAgendaTemplates, obj))


class AgendaTemplatesPermissionTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        register_security_policies(self.config)
        
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.agenda_templates import AgendaTemplates
        return AgendaTemplates

    def test_view(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.VIEW), admin)

    def test_edit(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.EDIT), admin)

    def test_delete(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.DELETE), set())

    def test_manage_server(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.MANAGE_SERVER), admin)

    def test_add_agenda_template(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.ADD_AGENDA_TEMPLATE), admin)
