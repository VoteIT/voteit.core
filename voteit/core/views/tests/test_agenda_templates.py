import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden
from pyramid_mailer import get_mailer


class AgendaTempalteViewTests(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        self.config.testing_securitypolicy(userid='admin',
                                           permissive=True)

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.agenda_templates import AgendaTempalteView
        return AgendaTempalteView

    def _fixture(self):
        from voteit.core.testing_helpers import bootstrap_and_fixture
        from voteit.core.testing_helpers import register_catalog
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.agenda_template import AgendaTemplate
        self.config.scan('voteit.core.schemas.agenda_template')
        self.config.scan('voteit.core.models.agenda_item')
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        register_catalog(self.config)
        root = bootstrap_and_fixture(self.config)
        at = AgendaTemplate()
        at.set_field_value('agenda_items', [{'description': u'Agenda Item 1', 'title': u'A1'},
                                            {'description': u'Agenda Item 2', 'title': u'A2'},
                                            {'description': u'Agenda Item 3', 'title': u'A3'},])
        root['agenda_templates']['dummy_template'] = at 
        root['m'] = Meeting()
        return root

    def test_agenda_templates(self):
        root = self._fixture()
        obj = self._cut(root['agenda_templates'], self.request)
        res = obj.agenda_templates()
        self.assertIn('agenda_templates', res)
        
    def test_agenda_template(self):
        root = self._fixture()
        obj = self._cut(root['agenda_templates']['dummy_template'], self.request)
        res = obj.agenda_template()
        self.assertIn('api', res)
        
    def test_agenda_template_select(self):
        self.config.include('voteit.core.models.flash_messages')
        root = self._fixture()
        request = testing.DummyRequest(GET = {'apply': 'dummy_template',},
                                       is_xhr = False)
        obj = self._cut(root['m'], request)
        res = obj.agenda_template_select()
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://example.com/m/')
        
    def test_agenda_template_select_invalid_template(self):
        self.config.include('voteit.core.models.flash_messages')
        root = self._fixture()
        request = testing.DummyRequest(GET = {'apply': 'dummy_template_invalid',},
                                       is_xhr = False)
        obj = self._cut(root['m'], request)
        res = obj.agenda_template_select()
        messages = tuple(res['api'].flash_messages.get_messages())
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['msg'], 'agenda_template_apply_invalid_template')
        
    def test_sort(self):
        root = self._fixture()
        obj = self._cut(root['agenda_templates'], self.request)
        res = obj.sort()
        self.assertEqual(res['title'], 'order_agenda_template_view_title')
        
    def test_sort_save(self):
        self.config.include('voteit.core.models.flash_messages')
        root = self._fixture()
        request = testing.DummyRequest(post = {'save': 'save', 
                                               'agenda_items': '0', 
                                               'agenda_items': '1', 
                                               'agenda_items': '2'},
                                       is_xhr = False)
        obj = self._cut(root['agenda_templates']['dummy_template'], request)
        res = obj.sort()
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://example.com/agenda_templates/dummy_template/')
        
    def test_sort_cancel(self):
        self.config.include('voteit.core.models.flash_messages')
        root = self._fixture()
        request = testing.DummyRequest(post = {'cancel': 'cancel',},
                                       is_xhr = False)
        obj = self._cut(root['agenda_templates']['dummy_template'], request)
        res = obj.sort()
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.location, 'http://example.com/agenda_templates/dummy_template/')