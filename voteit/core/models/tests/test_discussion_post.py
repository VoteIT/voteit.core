import unittest

from pyramid import testing
from pyramid.request import apply_request_extensions
from pyramid.security import principals_allowed_by_permission
from voteit.core.testing_helpers import bootstrap_and_fixture
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core import security
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


class DiscussionPostPermissionTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        """ DiscussionPosts check parents state and change their ACL depending
            on what state the meeting or agenda item is in.
        """
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.discussion_post import DiscussionPost
        root = bootstrap_and_fixture(self.config)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self.config.begin(request)
        root['m'] = m = Meeting()
        m['ai'] = AgendaItem()
        m['ai']['d'] = DiscussionPost()
        self.config.include('voteit.core.testing_helpers.register_security_policies')
        self.config.include('voteit.core.models.discussion_post')
        return m

    def test_upcoming_meeting_private_ai(self):
        m = self._fixture()
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.EDIT), admin | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), admin | moderator)
        
    def test_upcoming_meeting_upcoming_ai(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m['ai'], 'upcoming')
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | viewer | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.EDIT), admin | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), admin | moderator | owner)

    def test_ongoing_meeting_upcoming_ai(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'upcoming')
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | viewer | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.EDIT), admin | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), admin | moderator | owner)

    def test_ongoing_meeting_ongoing_ai(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'upcoming')
        security.unrestricted_wf_transition_to(m['ai'], 'ongoing')
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | viewer | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.EDIT), admin  | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), admin | moderator | owner)

    def test_ongoing_meeting_closed_ai(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'upcoming')
        security.unrestricted_wf_transition_to(m['ai'], 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'closed')
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | viewer | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.EDIT), admin  | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), admin | moderator | owner)

    def test_closed_meeting_closed_ai(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'closed')
        security.unrestricted_wf_transition_to(m, 'closed')
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | viewer | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.EDIT), set())
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), set())
