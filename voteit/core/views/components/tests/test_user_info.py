import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden
from betahaus.viewcomponent import render_view_action

from voteit.core.testing_helpers import bootstrap_and_fixture


class UserBasicProfileTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.components.user_info import user_basic_profile
        return user_basic_profile

    def test_func(self):
        from voteit.core.views.api import APIView
        root = _fixture(self.config)
        context = root['users']['admin']
        request = testing.DummyRequest()
        api = APIView(context, request)
        res = self._fut(context, request, None, api=api)
        self.assertIn("The story of an administrator", res)

    def test_integration(self):
        from voteit.core.models.user import User
        from voteit.core.views.api import APIView
        self.config.scan('voteit.core.views.components.user_info')
        context = User()
        request = testing.DummyRequest()
        api = APIView(context, request)
        self.assertIsInstance(render_view_action(context, request, 'user_info', 'basic_profile', api=api), unicode)


class UserLatestMeetingEntries(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.components.user_info import user_latest_meeting_entries
        return user_latest_meeting_entries

    def _extra_fixtures(self, root):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        from voteit.core.models.discussion_post import DiscussionPost
        from voteit.core.models.catalog import reindex_indexes
        settings = self.config.registry.settings
        settings['default_locale_name'] = 'sv'
        settings['default_timezone_name'] = 'Europe/Stockholm'
        self.config.include('voteit.core.models.date_time_util')
        root['m']['p1'] = Proposal(creators = ['admin'])
        root['m']['p1'].title = u"Prop p1"
        root['m']['d1'] = DiscussionPost(creators = ['admin'])
        root['m']['d1'].title = u"Disc d1"
        root['m2'] = Meeting()
        root['m2']['p2'] = Proposal(creators = ['admin'])
        root['m2']['p2'].title = u"Prop p2"
        root['m2']['d2'] = DiscussionPost(creators = ['admin'])
        root['m2']['d2'].title = u"Disc d2"
        reindex_indexes(root.catalog)

    def test_func_context_outside_meeting(self):
        from voteit.core.views.api import APIView
        root = _fixture(self.config)
        self._extra_fixtures(root)
        context = root['users']['admin']
        request = testing.DummyRequest()
        api = APIView(context, request)
        res = self._fut(context, request, None, api=api)
        #All things should be in view now
        self.assertIn("Prop p1", res)
        self.assertIn("Disc d2", res)

    def test_func_context_meeting(self):
        from voteit.core.views.api import APIView
        root = _fixture(self.config)
        self._extra_fixtures(root)
        context = root['users']['admin']
        request = testing.DummyRequest()
        #Means that api.meeting will be set, and limit results to meeting context
        api = APIView(root['m'], request)
        res = self._fut(context, request, None, api=api)
        #m2 things shouldn't be in meeting now
        self.assertIn("Prop p1", res)
        self.assertIn("Disc d1", res)
        self.assertNotIn("Prop p2", res)
        self.assertNotIn("Disc d2", res)

    def test_integration(self):
        from voteit.core.models.user import User
        from voteit.core.views.api import APIView
        self.config.scan('voteit.core.views.components.user_info')
        root = _fixture(self.config)
        root['u'] = context = User()
        request = testing.DummyRequest()
        api = APIView(context, request)
        self.assertIsInstance(render_view_action(context, request, 'user_info', 'latest_meeting_entries', api=api), unicode)


def _fixture(config):
    from voteit.core.models.meeting import Meeting
    config.testing_securitypolicy(userid='dummy', permissive=True)
    config.include('voteit.core.testing_helpers.register_catalog')
    root = bootstrap_and_fixture(config)
    root['users']['admin'].set_field_value('about_me', u"The story of an administrator")
    root['m'] = Meeting()
    return root
