import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden

from voteit.core.testing_helpers import bootstrap_and_fixture


class UserinfoTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _fixture(self):
        """ Normal context for this view is an agenda item. """
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.poll import Poll
        self.config.include('voteit.core.plugins.majority_poll')
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        return meeting
    
    def test__strip_and_truncate(self):
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris at enim nec nunc facilisis semper. Sed vel magna sit amet augue aliquet rhoncus metus."
        from voteit.core.views.userinfo import _strip_and_truncate
        truncated = _strip_and_truncate(text)
        self.assertEqual(truncated, 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris at enim nec nunc facilisis semper. S&lt;...&gt;') 
        
    def test_user_info_view(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(params={'userid': 'admin'}, is_xhr=True)
        from voteit.core.views.userinfo import user_info_view
        response = user_info_view(context, request)
        self.assertEqual(response.status, '200 OK')
        self.assertIn('VoteIT Administrator', response.body)
        
    def test_user_info_view_no_userid(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(is_xhr=True)
        from voteit.core.views.userinfo import user_info_view
        self.assertRaises(ValueError, user_info_view, context, request) 
        
    def test_user_info_view_invalid_userid(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(params={'userid': 'dummy'}, is_xhr=True)
        from voteit.core.views.userinfo import user_info_view
        self.assertRaises(ValueError, user_info_view, context, request)
        
    def test_user_info_view_no_xhr(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(params={'userid': 'admin'}, is_xhr=False)
        from voteit.core.views.userinfo import user_info_view
        self.assertRaises(HTTPForbidden, user_info_view, context, request)
        
    def test_user_info_view_user_context(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        self.config.include('voteit.core.models.date_time_util')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        meeting = self._fixture()
        context = meeting.__parent__.users['admin']
        request = testing.DummyRequest(params={'userid': 'admin'}, is_xhr=False)
        from voteit.core.views.userinfo import user_info_view
        response = user_info_view(context, request)
        self.assertIn('VoteIT Administrator', response)