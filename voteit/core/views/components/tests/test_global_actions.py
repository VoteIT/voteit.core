import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class GlobalActionsComponentTests(unittest.TestCase):
        
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        return meeting
    
    def _api(self, context=None, request=None):
        from voteit.core.views.api import APIView
        context = context and context or testing.DummyResource()
        request = request and request or testing.DummyRequest()
        return APIView(context, request)

    def _va(self, name=None, title=None, kwargs={}):
        class ViewAction():
            def __init__(self, name, title, kwargs):
                self.name = name
                self.title = title
                self.kwargs = kwargs
        return ViewAction(name, title, kwargs)
        
    def test_global_actions_authenticated(self):
        self.config.scan('voteit.core.views.components.global_actions')
        self.config.testing_securitypolicy(userid='admin', permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.global_actions import global_actions
        response = global_actions(context, request, va, api=api)
        self.assertTrue(response)

    def test_global_actions_anon(self):
        self.config.scan('voteit.core.views.components.global_actions')
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.global_actions import global_actions
        response = global_actions(context, request, va, api=api)
        self.assertFalse(response)

    def test_logout_action(self):
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.global_actions import logout_action
        response = logout_action(context, request, va, api=api)
        self.assertEqual('<li><a href="http://example.com/logout" class="logout icon"><span>Logout</span></a></li>', response)