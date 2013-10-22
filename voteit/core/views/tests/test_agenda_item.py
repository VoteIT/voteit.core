import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_security_policies
from voteit.core.models.date_time_util import utcnow


class AgendaItemViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.agenda_item import AgendaItemView
        return AgendaItemView
    
    def _fixture(self):
        """ Normal context for this view is an agenda item. """
        from voteit.core.models.user import User
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.poll import Poll
        self.config.include('voteit.core.plugins.majority_poll')
        root = bootstrap_and_fixture(self.config)
        root.users['dummy'] = User()
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        ai['poll'] = Poll(start_time = utcnow(), end_time = utcnow())
        ai['poll'].set_field_value('poll_plugin', 'majority_poll')
        return ai

    def _load_vcs(self):
        self.config.scan('voteit.core.views.components.main')
        self.config.scan('voteit.core.views.components.poll')
        self.config.scan('voteit.core.views.components.agenda_item')
        self.config.scan('voteit.core.views.components.proposals')
        self.config.scan('voteit.core.views.components.discussions')
        self.config.scan('voteit.core.views.components.moderator_actions')
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        
    def test_agenda_item_view(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(is_xhr=False)
        obj = self._cut(context, request)
        response = obj.agenda_item_view()
        self.assertIn('ai_columns', response) #Silly, but better than nothing

    def test_agenda_item_view_wrong_plugin(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self.config.include('voteit.core.models.flash_messages')
        self._load_vcs()
        context = self._fixture()
        context['poll'].set_field_value('poll_plugin', '')
        request = testing.DummyRequest(is_xhr=False)
        obj = self._cut(context, request)
        response = obj.agenda_item_view()
        self.assertIn('ai_columns', response) #Silly, but better than nothing

    def test_inline_add_form_no_permission(self):
        register_security_policies(self.config)
        self.config.scan('voteit.core.models.proposal')
        self.config.scan('voteit.core.schemas.proposal')
        context = self._fixture()
        request = testing.DummyRequest(params={'content_type': 'Proposal'})
        obj = self._cut(context, request)
        self.assertRaises(HTTPForbidden, obj.inline_add_form)

    def test_inline_add_form_proposal(self):
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self.config.scan('voteit.core.models.proposal')
        self.config.scan('voteit.core.schemas.proposal')
        context = self._fixture()
        request = testing.DummyRequest(params={'content_type': 'Proposal'})
        aiv = self._cut(context, request)
        response = aiv.inline_add_form()
        self.assertIn(u"content_type=Proposal", response.ubody)
        
    def test_inline_add_form_discussion_post(self):
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self.config.scan('voteit.core.models.discussion_post')
        self.config.scan('voteit.core.schemas.discussion_post')
        context = self._fixture()
        request = testing.DummyRequest(params={'content_type': 'DiscussionPost'})
        aiv = self._cut(context, request)
        response = aiv.inline_add_form()
        self.assertIn(u"content_type=DiscussionPost", response.ubody)
        
    def test_discussion_more(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self.config.include('voteit.core.models.fanstatic_resources')
        ai = self._fixture()
        from voteit.core.models.discussion_post import DiscussionPost
        ai['dp'] = context = DiscussionPost()
        context.title = "Testing read more view"
        request = testing.DummyRequest()
        aiv = self._cut(context, request)
        response = aiv.discussion_more()
        self.assertEqual(response['body'], context.title)

    def test_discussions_no_ajax(self):
        self.config.scan('voteit.core.views.components.discussions')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(is_xhr = False)
        obj = self._cut(context, request)
        res = obj.discussions()
        self.assertEqual(res.location, 'http://example.com/m/ai/#discussions')

    def test_discussions_no_ajax_load_all(self):
        self.config.scan('voteit.core.views.components.discussions')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(is_xhr = False,
                                       params = {'discussions': 'all'})
        obj = self._cut(context, request)
        res = obj.discussions()
        self.assertEqual(res.location, 'http://example.com/m/ai/?discussions=all#discussions')

    def test_discussions_w_ajax(self):
        self.config.scan('voteit.core.views.components.discussions')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(is_xhr = True)
        obj = self._cut(context, request)
        res = obj.discussions()
        self.assertEqual(res.status, '200 OK')
