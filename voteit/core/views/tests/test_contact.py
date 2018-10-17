import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden
from pyramid_mailer import get_mailer

from voteit.core.testing_helpers import bootstrap_and_fixture


def _fixture(config):
    from voteit.core.models.meeting import Meeting
    config.include('arche.testing')
    config.include('voteit.core.schemas.contact')
    config.include('pyramid_mailer.testing')
    root = bootstrap_and_fixture(config)
    request = testing.DummyRequest(root=root)
    config.begin(request)
    root['m'] = Meeting()
    return root, request


class SupportFormTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.testing_securitypolicy(userid='admin', permissive=True)
        self.config.include('pyramid_chameleon')
  
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.contact import SupportForm
        return SupportForm

    def test_no_support_email(self):
        context, request = _fixture(self.config)
        obj = self._cut(context, request)
        self.assertRaises(HTTPForbidden, obj)

    def test_render(self):
        context, request = _fixture(self.config)
        context.set_field_value('support_email', 'hello@bla.com')
        request.profile = None
        obj = self._cut(context, request)
        self.assertIn('form', obj())

    def test_post(self):
        postdata = {'send': 'send',
                    'name': 'Dummy Dumbson',
                    'subject': 'Test',
                    'email': 'dummy@test.com',
                    'message': 'Lorem ipsum',}
        context, request = _fixture(self.config)
        context.support_email = 'hello@bla.com'
        request = testing.DummyRequest(method = 'POST', POST = postdata, root = context, profile = None, meeting = None)
        obj = self._cut(context, request)
        response = obj()
        self.assertEqual(response.location, 'http://example.com/')
        mailer = get_mailer(request)
        self.assertTrue(mailer.outbox)
