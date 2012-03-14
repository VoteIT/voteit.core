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
        
        for userid in ('fredrik', 'anders', 'hanna', 'robin'):
            root.users[userid] = User()

        return root

    @property
    def _fut(self):
        from voteit.core.models.unread import Unread
        return Unread
    
    def _make_proposal(self):
        """ Since it also implements UnreadAware and has required security mixin. """
        from voteit.core.models.proposal import Proposal
        return Proposal()

    def test_verify_class(self):
        self.assertTrue(verifyClass(IUnread, self._fut))

    def test_verify_obj(self):
        register_security_policies(self.config)
        root = self._fixture_and_setup()
        context = self._make_proposal()
        root['c'] = context
        obj = self._fut(context)
        self.assertTrue(verifyObject(IUnread, obj))

    def test_mark_as_read(self):
        register_security_policies(self.config)
        root = self._fixture_and_setup()
        context = self._make_proposal()
        root['c'] = context
        obj = self._fut(context)
        userid = 'somebody'
        obj.unread_storage.add(userid)
        self.assertTrue(userid in obj.get_unread_userids())
        obj.mark_as_read(userid)
        self.assertFalse(userid in obj.get_unread_userids())

    def test_unread_on_check(self):
        register_security_policies(self.config)
        root = self._fixture_and_setup()
        prop = self._make_proposal()
        root['new'] = prop
        obj = self._fut(prop)
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin',)))

    def test_only_viewers_added(self):
        register_security_policies(self.config)
        root = self._fixture_and_setup()
        prop = self._make_proposal()
        root['new'] = prop
        prop.add_groups('hanna', [security.ROLE_VIEWER])
        prop.add_groups('anders', [security.ROLE_VIEWER])
        obj = self._fut(prop)
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin', 'hanna', 'anders')))

    def test_reset_unread(self):
        register_security_policies(self.config)
        root = self._fixture_and_setup()
        prop = self._make_proposal()
        root['new'] = prop
        prop.add_groups('hanna', [security.ROLE_VIEWER])
        prop.add_groups('anders', [security.ROLE_VIEWER])
        obj = self._fut(prop)
        obj.mark_as_read('hanna')
        obj.reset_unread()
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin', 'hanna', 'anders')))