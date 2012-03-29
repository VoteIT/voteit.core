import unittest

from pyramid import testing

#from voteit.core.testing_helpers import bootstrap_and_fixture


class SearchViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.api import APIView
        return APIView

    def test_authn_policy(self):
        self.config.testing_securitypolicy('dummy')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.authn_policy)

    def test_authz_policy(self):
        self.config.testing_securitypolicy('dummy')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.authz_policy)

#FIXME: Write more tests :)