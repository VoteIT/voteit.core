import unittest
 
from pyramid import testing
from arche.api import Content
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
 
from voteit.core import security
from voteit.core.testing_helpers import bootstrap_and_fixture
#from voteit.core.models.interfaces import IUnread
from voteit.core.models.interfaces import IUserUnread


class UserUnreadTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
        self.config.include('arche.testing')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.unread import UserUnread
        return UserUnread

    def test_verify_class(self):
        self.assertTrue(verifyClass(IUserUnread, self._cut))

    def test_verify_obj(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        self.assertTrue(verifyObject(IUserUnread, obj))

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai1'] = ai = AgendaItem(uid='uid_ai1')
        ai['p1'] = Proposal(uid='uid_p1')
        ai['p2'] = Proposal(uid='uid_p2')
        return root

    def test_add(self):
        root = self._fixture()
        proposal = root['m']['ai1']['p1']
        obj = self._cut(root)
        obj.add(proposal)
        self.assertIn('Proposal', obj['uid_ai1'])
        self.assertIn('uid_p1', obj['uid_ai1']['Proposal'])

    def test_remove(self):
        root = self._fixture()
        proposal = root['m']['ai1']['p1']
        obj = self._cut(root)
        obj.add(proposal)
        self.assertIn('uid_p1', obj['uid_ai1']['Proposal'])
        obj.remove(proposal)
        self.assertNotIn('uid_p1', obj['uid_ai1']['Proposal'])

    def test_get_count(self):
        root = self._fixture()
        obj = self._cut(root)
        self.assertEqual(obj.get_count('uid_ai1', 'Proposal'), 0)
        obj.add(root['m']['ai1']['p1'])
        self.assertEqual(obj.get_count('uid_ai1', 'Proposal'), 1)
        obj.add(root['m']['ai1']['p2'])
        self.assertEqual(obj.get_count('uid_ai1', 'Proposal'), 2)

    def test_get_uids(self):
        root = self._fixture()
        obj = self._cut(root)
        self.assertEqual(obj.get_uids('uid_ai1', 'Proposal'), ())
        obj.add(root['m']['ai1']['p1'])
        self.assertEqual(obj.get_uids('uid_ai1', 'Proposal'), frozenset(['uid_p1']))
        obj.add(root['m']['ai1']['p2'])
        self.assertEqual(obj.get_uids('uid_ai1', 'Proposal'), frozenset(['uid_p1', 'uid_p2']))


class UserUnreadIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
        self.config.include('arche.testing')
        self.config.include('arche.testing.setup_auth')
        self.config.include('voteit.core.models.unread')
        self.config.include('voteit.core.models.meeting')

    def tearDown(self):
        testing.tearDown()

    def _fixture_and_setup(self):
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.user import User
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root['m'] = meeting = Meeting()
        for userid in ('fredrik', 'anders', 'hanna', 'robin'):
            root.users[userid] = User()
            meeting.local_roles.add(userid, security.ROLE_VIEWER)
        root['m']['ai'] = ai = AgendaItem(uid='ai_uid')
        security.unrestricted_wf_transition_to(ai, 'upcoming')
        ai['p'] = Proposal()
        return root

    def test_integration(self):
        root = self._fixture_and_setup()
        user = root['users']['fredrik']
        ai = root['m']['ai']
        unread = IUserUnread(user)
        self.assertEqual(unread.get_count('ai_uid', 'Proposal'), 1)
        del ai['p']
        self.assertEqual(unread.get_count('ai_uid', 'Proposal'), 0)


# class UnreadTests(unittest.TestCase):
#
#     def setUp(self):
#         self.config = testing.setUp(request = testing.DummyRequest())
#         self.config.include('arche.testing')
#         self.config.include('arche.testing.setup_auth')
#         self.config.include('voteit.core.models.meeting')
#
#     def tearDown(self):
#         testing.tearDown()
#
#     def _fixture_and_setup(self):
#         root = bootstrap_and_fixture(self.config)
#         from voteit.core.models.user import User
#         from voteit.core.models.agenda_item import AgendaItem
#         from voteit.core.models.meeting import Meeting
#         from voteit.core.models.proposal import Proposal
#         for userid in ('fredrik', 'anders', 'hanna', 'robin'):
#             root.users[userid] = User()
#         root['m'] = Meeting()
#         root['m']['ai'] = ai = AgendaItem()
#         security.unrestricted_wf_transition_to(ai, 'upcoming')
#         ai['p'] = Proposal()
#         return ai['p']
#
#     @property
#     def _cut(self):
#         from voteit.core.models.unread import Unread
#         return Unread
#
#     def test_verify_class(self):
#         self.assertTrue(verifyClass(IUnread, self._cut))
#
#     def test_verify_obj(self):
#         context = self._fixture_and_setup()
#         obj = self._cut(context)
#         self.assertTrue(verifyObject(IUnread, obj))
#
#     def test_mark_as_read(self):
#         context = self._fixture_and_setup()
#         obj = self._cut(context)
#         userid = 'somebody'
#         obj.unread_storage.add(userid)
#         self.assertTrue(userid in obj.get_unread_userids())
#         obj.mark_as_read(userid)
#         self.assertFalse(userid in obj.get_unread_userids())
#
#     def test_unread_on_check(self):
#         context = self._fixture_and_setup()
#         obj = self._cut(context)
#         self.assertEqual(obj.get_unread_userids(), frozenset(('admin',)))
#
#     def test_only_viewers_added(self):
#         context = self._fixture_and_setup()
#         meeting = context.__parent__.__parent__
#         meeting.add_groups('hanna', [security.ROLE_VIEWER])
#         meeting.add_groups('anders', [security.ROLE_VIEWER])
#         obj = self._cut(context)
#         self.assertEqual(obj.get_unread_userids(), frozenset(('admin', 'hanna', 'anders')))
#
#     def test_reset_unread(self):
#         context = self._fixture_and_setup()
#         meeting = context.__parent__.__parent__
#         meeting.add_groups('hanna', [security.ROLE_VIEWER])
#         meeting.add_groups('anders', [security.ROLE_VIEWER])
#         obj = self._cut(context)
#         obj.mark_as_read('hanna')
#         obj.reset_unread()
#         self.assertEqual(obj.get_unread_userids(), frozenset(('admin', 'hanna', 'anders')))
#
#     def test_integration(self):
#         context = self._fixture_and_setup()
#         self.config.include('voteit.core.models.unread')
#         self.failUnless(IUnread(context, None))
