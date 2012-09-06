import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class HelpActionsComponentTests(unittest.TestCase):
        
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
        
    def test_help_actions(self):
        self.config.scan('voteit.core.views.components.help_actions')
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.help_actions import help_actions
        response = help_actions(context, request, va, api=api)
        self.assertIn('<ul id="help-actions">', response)
        
    def test_action_wiki(self):
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.help_actions import action_wiki
        response = action_wiki(context, request, va, api=api)
        self.assertEqual('<li><a class="buttonize" href="http://wiki.voteit.se" target="_blank">VoteIT Wiki</a></li>', response)
        
    def test_action_contact(self):
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.help_actions import action_contact
        response = action_contact(context, request, va, api=api)
        self.assertEqual('<li><a class="tab buttonize" href="http://example.com/m/contact">Contact</a></li>', response)
        
    def test_action_contact_no_meeting(self):
        context = bootstrap_and_fixture(self.config)
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.help_actions import action_contact
        response = action_contact(context, request, va, api=api)
        self.assertEqual('', response)