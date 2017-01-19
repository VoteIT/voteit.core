import unittest

from pyramid import testing
from betahaus.viewcomponent import render_view_action
from arche.views.base import BaseView

from voteit.core.testing_helpers import bootstrap_and_fixture
from arche.models.datetime_handler import DateTimeHandler


class UserBasicProfileTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
        self.config.include('pyramid_chameleon')

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.components.user_info import user_basic_profile
        return user_basic_profile

    def test_func(self):
        root = _fixture(self.config)
        context = root['users']['admin']
        request = testing.DummyRequest()
        res = self._fut(context, request, None)
        self.assertIn("The story of an administrator", res)

    def test_integration(self):
        from voteit.core.models.user import User
        self.config.scan('voteit.core.views.components.user_info')
    
        context = User()
        request = testing.DummyRequest()
        self.assertIsInstance(render_view_action(context, request, 'user_info', 'basic_profile'), unicode)


class UserLatestMeetingEntries(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
        self.config.include('pyramid_chameleon')

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
        settings = self.config.registry.settings
        root['m']['p1'] = Proposal(text = u"Prop p1", creators = ['admin'])
        root['m']['d1'] = DiscussionPost(text = "Disc d1", creators = ['admin'])
        root['m2'] = Meeting()
        root['m2']['p2'] = Proposal(text = u"Prop p2", creators = ['admin'])
        root['m2']['d2'] = DiscussionPost(text = u"Disc d2", creators = ['admin'])

    def test_func_context_outside_meeting(self):
        root = _fixture(self.config)
        self._extra_fixtures(root)
        context = root['users']['admin']
        request = testing.DummyRequest()
        request.meeting = None
        request.root = root
        request.dt_handler = DateTimeHandler(request)
        view = BaseView(context, request)
        res = self._fut(context, request, None, view = view)
        #All things should be in view now
        self.assertIn("Prop p1", res)
        self.assertIn("Disc d2", res)

    def test_func_context_meeting(self):
        root = _fixture(self.config)
        self._extra_fixtures(root)
        context = root['users']['admin']
        request = testing.DummyRequest()
        request.root = root
        request.meeting = root['m']
        request.dt_handler = DateTimeHandler(request)
        view = BaseView(context, request)
        res = self._fut(context, request, None, view = view)
        #m2 things shouldn't be in meeting now
        self.assertIn("Prop p1", res)
        self.assertIn("Disc d1", res)
        self.assertNotIn("Prop p2", res)
        self.assertNotIn("Disc d2", res)

    def test_integration(self):
        from voteit.core.models.user import User
        self.config.scan('voteit.core.views.components.user_info')
        root = _fixture(self.config)
        root['u'] = context = User()
        request = testing.DummyRequest(context = context)
        request.meeting = None
        request.root = root
        view = BaseView(context, request)
        self.assertIsInstance(render_view_action(context, request, 'user_info', 'latest_meeting_entries', view = view), unicode)


def _fixture(config):
    from voteit.core.models.meeting import Meeting
    config.testing_securitypolicy(userid='dummy', permissive=True)
    config.include('voteit.core.testing_helpers.register_catalog')
    root = bootstrap_and_fixture(config)
    root['users']['admin'].about_me = u"The story of an administrator"
    root['m'] = Meeting()
    return root
