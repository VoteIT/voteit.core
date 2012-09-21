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
        
    def test_title_tags(self):
        obj = self._cut()
        obj.title = '#Quisque #aliquam,#ante in #tincidunt #aliquam. #Risus neque#eleifend #nunc'
        self.assertIn('quisque', obj._tags)
        self.assertIn('aliquam', obj._tags)
        self.assertIn('ante', obj._tags)
        self.assertIn('tincidunt', obj._tags)
        self.assertIn('aliquam', obj._tags)
        self.assertIn('risus', obj._tags)
        self.assertIn('nunc', obj._tags)
        self.assertNotIn('eleifend', obj._tags)
        
    def test_mentioned(self):
        obj = self._cut()
        obj.mentioned['dummy'] = 'now'
        self.assertIn('dummy', obj.mentioned)
        
    def test_add_mention(self):
        obj = self._cut()
        obj.add_mention('dummy')
        self.assertIn('dummy', obj.mentioned)


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
        """ DiscussionPosts check parents state and change their ACL depending
            on what state the meeting or agenda item is in.
        """
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.discussion_post import DiscussionPost
        m = Meeting()
        m['ai'] = AgendaItem()
        m['ai']['d'] = DiscussionPost()
        return m

    def test_upcoming_meeting_private_ai(self):
        m = self._fixture()
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), admin | moderator)
        
    def test_upcoming_meeting_upcoming_ai(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m['ai'], 'upcoming')
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | viewer | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), admin | moderator | owner)

    def test_ongoing_meeting_upcoming_ai(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'upcoming')
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | viewer | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), admin | moderator | owner)

    def test_ongoing_meeting_ongoing_ai(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'upcoming')
        security.unrestricted_wf_transition_to(m['ai'], 'ongoing')
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | viewer | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), admin | moderator | owner)

    def test_ongoing_meeting_closed_ai(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'upcoming')
        security.unrestricted_wf_transition_to(m['ai'], 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'closed')
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | viewer | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), admin | moderator | owner)

    def test_closed_meeting_closed_ai(self):
        m = self._fixture()
        security.unrestricted_wf_transition_to(m, 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'upcoming')
        security.unrestricted_wf_transition_to(m['ai'], 'ongoing')
        security.unrestricted_wf_transition_to(m['ai'], 'closed')
        security.unrestricted_wf_transition_to(m, 'closed')
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.VIEW), admin | viewer | moderator)
        self.assertEqual(principals_allowed_by_permission(m['ai']['d'], security.DELETE), set())
