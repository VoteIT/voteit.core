import unittest

from pyramid import testing
from zope.interface.verify import verifyObject


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