import unittest

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from BTrees.OOBTree import OOSet
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy

from voteit.core import security
from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_security_policies
from voteit.core.models.interfaces import IUnread





class UnreadTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _fixture_and_setup(self):
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.user import User
        from voteit.core.models.agenda_item import AgendaItem
        #from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        for userid in ('fredrik', 'anders', 'hanna', 'robin'):
            root.users[userid] = User()
        root['ai'] = AgendaItem()
        security.unrestricted_wf_transition_to(root['ai'], 'upcoming')
        root['ai']['p'] = Proposal()
        return root['ai']['p']

    @property
    def _cut(self):
        from voteit.core.models.unread import Unread
        return Unread

    def test_verify_class(self):
        self.assertTrue(verifyClass(IUnread, self._cut))

    def test_verify_obj(self):
        register_security_policies(self.config)
        context = self._fixture_and_setup()
        obj = self._cut(context)
        self.assertTrue(verifyObject(IUnread, obj))

    def test_mark_as_read(self):
        register_security_policies(self.config)
        context = self._fixture_and_setup()
        obj = self._cut(context)
        userid = 'somebody'
        obj.unread_storage.add(userid)
        self.assertTrue(userid in obj.get_unread_userids())
        obj.mark_as_read(userid)
        self.assertFalse(userid in obj.get_unread_userids())

    def test_unread_on_check(self):
        register_security_policies(self.config)
        context = self._fixture_and_setup()
        obj = self._cut(context)
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin',)))

    def test_only_viewers_added(self):
        register_security_policies(self.config)
        context = self._fixture_and_setup()
        context.add_groups('hanna', [security.ROLE_VIEWER])
        context.add_groups('anders', [security.ROLE_VIEWER])
        obj = self._cut(context)
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin', 'hanna', 'anders')))

    def test_reset_unread(self):
        register_security_policies(self.config)
        context = self._fixture_and_setup()
        context.add_groups('hanna', [security.ROLE_VIEWER])
        context.add_groups('anders', [security.ROLE_VIEWER])
        obj = self._cut(context)
        obj.mark_as_read('hanna')
        obj.reset_unread()
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin', 'hanna', 'anders')))
