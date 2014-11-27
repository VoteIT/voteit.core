import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden
from pyramid_mailer import get_mailer

from voteit.core.testing_helpers import bootstrap_and_fixture


def _fixture(config):
    from voteit.core.models.meeting import Meeting
    config.scan('voteit.core.schemas.contact')
    config.include('voteit.core.models.flash_messages')
    config.include('pyramid_mailer.testing')
    root = bootstrap_and_fixture(config)
    root['m'] = Meeting()
    return root


class ContactViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.testing_securitypolicy(userid='admin', permissive=True)
 
    def tearDown(self):
        testing.tearDown()
 
    @property
    def _cut(self):
        from voteit.core.views.contact import ContactView
        return ContactView

    def test_render(self):
        context = _fixture(self.config)
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertIn('form', obj())

    def test_post(self):
        postdata = {'send': 'send',
                    'name': 'Dummy Dumbson',
                    'subject': 'Test',
                    'email': 'dummy@test.com',
                    'message': 'Lorem ipsum',}
        context = _fixture(self.config)
        request = testing.DummyRequest(method = 'POST', post = postdata)
        obj = self._cut(context, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/')
        mailer = get_mailer(request)
        self.assertTrue(mailer.outbox)


class SupportFormTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.testing_securitypolicy(userid='admin', permissive=True)
 
    def tearDown(self):
        testing.tearDown()
 
    @property
    def _cut(self):
        from voteit.core.views.contact import SupportForm
        return SupportForm

    def test_no_support_email(self):
        context = _fixture(self.config)
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertRaises(HTTPForbidden, obj)

    def test_render(self):
        context = _fixture(self.config)
        context.set_field_value('support_email', 'hello@bla.com')
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertIn('form', obj())

    def test_post(self):
        postdata = {'send': 'send',
                    'name': 'Dummy Dumbson',
                    'subject': 'Test',
                    'email': 'dummy@test.com',
                    'message': 'Lorem ipsum',}
        context = _fixture(self.config)
        context.set_field_value('support_email', 'hello@bla.com')
        request = testing.DummyRequest(method = 'POST', post = postdata)
        obj = self._cut(context, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/')
        mailer = get_mailer(request)
        self.assertTrue(mailer.outbox)
