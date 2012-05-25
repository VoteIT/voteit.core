import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class RequestAccessComponentTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        return meeting
    
    def _api(self, context=None, request=None):
        from voteit.core.views.api import APIView
        context = context and context or testing.DummyResource()
        request = request and request or testing.DummyRequest()
        return APIView(context, request)

    def _va(self):
        class ViewAction():
            pass
        return ViewAction()
        
    def test_public_request_meeting_access_not_set(self):
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context)
        from voteit.core.views.components.request_access import public_request_meeting_access
        self.assertRaises(Exception, public_request_meeting_access, context, request, va, api=api)
        
    def test_public_request_meeting_access(self):
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        context.set_field_value('access_policy', 'public')
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.request_access import public_request_meeting_access
        response = public_request_meeting_access(context, request, va, api=api)
        self.assertIn('<form', response)
        
    def test_public_request_meeting_access_request(self):
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        context.set_field_value('access_policy', 'public')
        request = testing.DummyRequest(post={'request': 'request'})
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.request_access import public_request_meeting_access
        response = public_request_meeting_access(context, request, va, api=api)
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_public_request_meeting_access_no_user(self):
        self.config.include('voteit.core.models.flash_messages')
        context = self._fixture()
        context.set_field_value('access_policy', 'public')
        request = testing.DummyRequest(post={'request': 'request'})
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.request_access import public_request_meeting_access
        self.assertRaises(Exception, public_request_meeting_access, context, request, va, api=api)
        
    def test_all_participant_permissions_meeting_access_not_set(self):
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context)
        from voteit.core.views.components.request_access import all_participant_permissions_meeting_access
        self.assertRaises(Exception, all_participant_permissions_meeting_access, context, request, va, api=api)
        
    def test_all_participant_permissions_meeting_access(self):
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        context.set_field_value('access_policy', 'all_participant_permissions')
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.request_access import all_participant_permissions_meeting_access
        response = all_participant_permissions_meeting_access(context, request, va, api=api)
        self.assertIn('<form', response)
        
    def test_all_participant_permissions_meeting_access_request(self):
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        context.set_field_value('access_policy', 'all_participant_permissions')
        request = testing.DummyRequest(post={'request': 'request'})
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.request_access import all_participant_permissions_meeting_access
        response = all_participant_permissions_meeting_access(context, request, va, api=api)
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_all_participant_permissions_meeting_access_no_user(self):
        self.config.include('voteit.core.models.flash_messages')
        context = self._fixture()
        context.set_field_value('access_policy', 'all_participant_permissions')
        request = testing.DummyRequest(post={'request': 'request'})
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.request_access import all_participant_permissions_meeting_access
        self.assertRaises(Exception, all_participant_permissions_meeting_access, context, request, va, api=api)
        
    def test_invite_only_request_meeting_access(self):
        self.config.include('voteit.core.models.flash_messages')
        context = self._fixture()
        request = testing.DummyRequest(post={'request': 'request'})
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.request_access import invite_only_request_meeting_access
        response = invite_only_request_meeting_access(context, request, va, api=api)
        self.assertEqual(response.location, 'http://example.com/')
