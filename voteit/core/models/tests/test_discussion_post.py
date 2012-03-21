import unittest

from pyramid import testing
from pyramid.url import resource_url
from pyramid.security import principals_allowed_by_permission
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core import security
from voteit.core.testing_helpers import register_security_policies
from voteit.core.models.interfaces import IDiscussionPost


admin = set([security.ROLE_ADMIN])
owner = set([security.ROLE_OWNER])
viewer = set([security.ROLE_VIEWER])
moderator = set([security.ROLE_MODERATOR])


class DiscussionTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.discussion_post import DiscussionPost
        return DiscussionPost

    def test_verify_class(self):
        self.assertTrue(verifyClass(IDiscussionPost, self._cut))

    def test_verify_obj(self):
        self.assertTrue(verifyObject(IDiscussionPost, self._cut()))

    def test_newline_to_br_enabled(self):
        obj = self._cut()
        obj.set_field_value('text', 'test\ntest')
        self.assertEqual(unicode(obj.get_field_value('text')), unicode('test<br /> test'))

    def test_autolinking_enabled(self):
        obj = self._cut()
        obj.set_field_value('text', 'www.betahaus.net')
        self.assertEqual(unicode(obj.get_field_value('text')), unicode('<a href="http://www.betahaus.net">www.betahaus.net</a>'))

    def test_title_and_text_linked(self):
        obj = self._cut()
        obj.set_field_value('title', "Hello")
        self.assertEqual(obj.get_field_value('text'), "Hello")

    def test_nl2br_several_runs_should_not_add_more_brs(self):
        obj = self._cut()
        obj.title = "Hello\nthere"
        res = obj.get_field_value('title')
        obj.title = res
        result = obj.get_field_value('title')
        self.assertEqual(result.count('<br />'), 1)


class DiscussionPostPermissionTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        register_security_policies(self.config)
        # load workflow
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()


    def _fixture(self):
        """ DiscussionPosts check the meetings state and change their ACL depending
            on what state the meeting is in
        """
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.discussion_post import DiscussionPost
        m = Meeting()
        m['d'] = DiscussionPost()
        return m

    def test_view_upcoming_meeting(self):
        m = self._fixture()
        self.assertEqual(principals_allowed_by_permission(m['d'], security.VIEW), admin | viewer | moderator)

    def test_view_ongoing_meeting(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        self.assertEqual(principals_allowed_by_permission(m['d'], security.VIEW), admin | viewer | moderator)

    def test_view_closed_meeting(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m, 'closed')
        self.assertEqual(principals_allowed_by_permission(m['d'], security.VIEW), admin | viewer | moderator)

    def test_edit_upcoming_meeting(self):
        m = self._fixture()
        self.assertEqual(principals_allowed_by_permission(m['d'], security.EDIT), set())

    def test_edit_ongoing_meeting(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        self.assertEqual(principals_allowed_by_permission(m['d'], security.EDIT), set())

    def test_edit_closed_meeting(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m, 'closed')
        self.assertEqual(principals_allowed_by_permission(m['d'], security.EDIT), set())

    def test_delete_upcoming_meeting(self):
        m = self._fixture()
        self.assertEqual(principals_allowed_by_permission(m['d'], security.DELETE), admin | moderator | owner)

    def test_delete_ongoing_meeting(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        self.assertEqual(principals_allowed_by_permission(m['d'], security.DELETE), admin | moderator | owner)

    def test_delete_closed_meeting(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m, 'closed')
        self.assertEqual(principals_allowed_by_permission(m['d'], security.DELETE), set())
