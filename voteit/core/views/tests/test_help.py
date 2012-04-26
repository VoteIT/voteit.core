import unittest

from deform.exception import ValidationFailure
from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden
from pyramid_mailer import get_mailer

from voteit.feed.interfaces import IFeedHandler


class HelpViewTests(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        self.config.testing_securitypolicy(userid='admin',
                                           permissive=True)

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.help import HelpView
        return HelpView

    def _fixture(self):
        from voteit.core.testing_helpers import bootstrap_and_fixture
        from voteit.core.testing_helpers import register_catalog
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        self.config.scan('voteit.core.schemas')
        self.config.include('pyramid_mailer.testing')
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        register_catalog(self.config)
        root = bootstrap_and_fixture(self.config)
        root['m'] = Meeting()
        root['m'].set_field_value('rss_feed', True)
        root['m']['ai'] = AgendaItem()
        root['m']['ai'].set_workflow_state(self.request, 'upcoming')
        return root

    def test_contact(self):
        root = self._fixture()
        obj = self._cut(root['m'], self.request)
        res = obj.contact()
        self.assertIn("Contact moderator", res['form'])

    def test_contact_post_without_ajax(self):
        root = self._fixture()
        request = testing.DummyRequest(post = {'save': 'save', 
                                               '__formid__': 'deform',
                                               'name': 'Dummy Dumbson',
                                               'email': 'dummy@test.com',
                                               'subject': 'Test',
                                               'message': 'Lorem ipsum',},
                                       is_xhr = False)
        obj = self._cut(root['m'], request)
        res = obj.contact()
        self.assertEqual(res.status, '200 OK')
        self.assertIn("Message sent to the moderators", res.text)
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)

    def test_contact_with_ajax(self):
        root = self._fixture()
        request = testing.DummyRequest(post = {'save': 'save', 
                                               '__formid__': 'deform',
                                               'name': 'Dummy Dumbson',
                                               'email': 'dummy@test.com',
                                               'subject': 'Test',
                                               'message': 'Lorem ipsum',},
                                       is_xhr = True)
        obj = self._cut(root['m'], request)
        res = obj.contact()
        self.assertEqual(res.status, '200 OK')
        self.assertIn("Message sent to the moderators", res.text)
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)

    def test_contact_validation_error(self):
        root = self._fixture()
        postdata = {'save': 'save', 
                    '__formid__': 'deform',
                    'name': 'Dummy Dumbson',
                    'email': 'dummy@test.com',
                    'message': 'Lorem ipsum',}
        request = testing.DummyRequest(post = postdata,
                                       is_xhr = False)
        obj = self._cut(root['m'], request)
        res = obj.contact()
        self.assertIn('form', res)
        # and with ajax
        request = testing.DummyRequest(post = postdata,
                                       is_xhr = True)
        obj = self._cut(root['m'], request)
        res = obj.contact()
        self.assertIn('form', res)