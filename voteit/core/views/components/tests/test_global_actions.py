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
        
    def test_global_actions(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.scan('voteit.core.views.components.global_actions')
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.global_actions import global_actions
        response = global_actions(context, request, va, api=api)
        self.assertTrue(response)
        
    def test_action_login(self):
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.global_actions import action_login
        response = action_login(context, request, va, api=api)
        self.assertEqual('<li><a href="http://example.com/login">Login</a></li>', response)
        
    def test_action_register(self):
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.global_actions import action_register
        response = action_register(context, request, va, api=api)
        self.assertEqual('<li><a href="http://example.com/register">Register</a></li>', response)
        
    def test_user_profile_action(self):
        self.config.testing_securitypolicy(userid='admin',
                                           permissive=True)
        
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.global_actions import user_profile_action
        response = user_profile_action(context, request, va, api=api)
        self.assertEqual('<li><a href="http://example.com/users/admin/" class="user icon"><span>VoteIT Administrator</span></a></li>', response)
        
    def test_logout_action(self):
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.global_actions import logout_action
        response = logout_action(context, request, va, api=api)
        self.assertEqual('<li><a href="http://example.com/logout" class="logout icon"><span>Logout</span></a></li>', response)