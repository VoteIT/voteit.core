import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden


class UnsupportedBrowserTests(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        self.config.testing_securitypolicy(userid='admin',
                                           permissive=True)

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.unsupported_browser import UnsupportedBrowser
        return UnsupportedBrowser

    def _fixture(self):
        from voteit.core.testing_helpers import bootstrap_and_fixture
        from voteit.core.testing_helpers import register_catalog
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        register_catalog(self.config)
        root = bootstrap_and_fixture(self.config)
        return root

    def test_contact(self):
        root = self._fixture()
        obj = self._cut(root, self.request)
        res = obj.unsupported_browser()
        self.assertIn('api', res)