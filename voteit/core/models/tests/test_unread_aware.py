import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from BTrees.OOBTree import OOSet

from voteit.core.bootstrap import bootstrap_voteit
from voteit.core.app import register_content_types
from voteit.core import security


class UnreadAwareTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _fixture_and_setup(self):
        self.config.registry.settings['content_types'] = """
        voteit.core.models.site
        voteit.core.models.user
        voteit.core.models.users
        """
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')
        register_content_types(self.config)

        root = bootstrap_voteit(registry=self.config.registry, echo=False)
        from voteit.core.models.user import User
        
        for userid in ('fredrik', 'anders', 'hanna', 'robin'):
            root.users[userid] = User()

        return root

    def _make_obj(self):
        from voteit.core.models.unread_aware import UnreadAware
        return UnreadAware()
    
    def _make_proposal(self):
        """ Since it also implements UnreadAware and has required security mixin. """
        from voteit.core.models.proposal import Proposal
        return Proposal()

    def _setup_security(self):
        self.config.setup_registry(authentication_policy=security.authn_policy,
                                   authorization_policy=security.authz_policy)

    def test_interface(self):
        from voteit.core.models.interfaces import IUnreadAware
        obj = self._make_obj()
        self.assertTrue(verifyObject(IUnreadAware, obj))

    def test_mark_as_read(self):
        obj = self._make_obj()
        userid = 'somebody'
        obj.unread_storage.add(userid)
        self.assertTrue(userid in obj.get_unread_userids())
        obj.mark_as_read(userid)
        self.assertFalse(userid in obj.get_unread_userids())

    def test_mark_all_unread(self):
        self._setup_security()
        root = self._fixture_and_setup()
        obj = self._make_proposal()
        root['new'] = obj
        obj.mark_all_unread()
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin',)))
        
    def test_subscriber_fired_and_added_users(self):
        self._setup_security()
        self.config.scan('voteit.core.subscribers.unread')
        root = self._fixture_and_setup()
        obj = self._make_proposal()
        root['new'] = obj
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin',)))

    def test_only_viewers_added_on_mark_all(self):
        self._setup_security()
        root = self._fixture_and_setup()
        obj = self._make_proposal()
        root['new'] = obj
        obj.add_groups('hanna', [security.ROLE_VIEWER])
        obj.add_groups('anders', [security.ROLE_VIEWER])
        obj.mark_all_unread()
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin', 'hanna', 'anders')))
