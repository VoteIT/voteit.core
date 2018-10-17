import unittest

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy

from voteit.core.bootstrap import bootstrap_voteit
from voteit.core import security


authn_policy = AuthTktAuthenticationPolicy(secret='sosecret',
                                           callback=security.groupfinder)
authz_policy = ACLAuthorizationPolicy()

ALL_TEST_USERS = set(('fredrik', 'anders', 'hanna', 'robin', 'admin'))

class SecurityTests(unittest.TestCase):
    """ Tests for methods in voteit.core.security.
    """
    
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
        self.config.include('voteit.core.testing_helpers.bootstrap_and_fixture')
        self.config.include('arche.testing.setup_auth')

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        root = bootstrap_voteit(echo=False)
        from voteit.core.models.user import User
        #Note that creators also fixes ownership
        for userid in ('fredrik', 'anders', 'hanna', 'robin'):
            root.users[userid] = User(creators = [userid])
        return root

    def test_find_authorized_userids_admin(self):
        root = self._fixture()
        res = security.find_authorized_userids(root, (security.ROLE_ADMIN,))
        self.assertEqual(res, set(('admin',)))
    
    def test_find_aithorized_userids_several_perms(self):
        root = self._fixture()
        root.add_groups('robin', ('role:Administrator',))
        res = security.find_authorized_userids(root, (security.VIEW, security.ROLE_ADMIN))
        self.assertEqual(res, set(('admin', 'robin')))

    def test_context_effective_principals_admin(self):
        root = self._fixture()
        res = set(security.context_effective_principals(root, 'admin'))
        self.assertEqual(res, set(['system.Everyone', 'system.Authenticated', 'admin', 'role:Administrator', 'role:Owner']))
        
    def test_context_effective_principals_normal_user(self):
        root = self._fixture()
        res = security.context_effective_principals(root, 'hanna')
        self.assertEqual(res, ['system.Everyone', 'system.Authenticated', 'hanna'])

    def test_context_effective_principals_unauthenticated(self):
        root = self._fixture()
        res = security.context_effective_principals(root, None)
        self.assertEqual(res, ['system.Everyone'])

    def test_groups_added_to_principals(self):
        root = self._fixture()
        root.add_groups('fredrik', ('group:developer', 'group:Betahaus',))
        res = security.context_effective_principals(root, 'fredrik')
        self.assertEqual(res, ['system.Everyone', 'system.Authenticated',
                               'fredrik', 'group:Betahaus', 'group:developer'])

    def test_roles_added_to_principals(self):
        root = self._fixture()
        root.add_groups('robin', ('role:Administrator',))
        res = security.context_effective_principals(root, 'robin')
        self.assertEqual(res, ['system.Everyone', 'system.Authenticated',
                               'robin', 'role:Administrator'])

    def test_find_role_userids(self):
        root = self._fixture()
        self.assertEqual(security.find_role_userids(root, 'role:Administrator'), frozenset(['admin']))

    def test_find_role_userids_other_context(self):
        root = self._fixture()
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.user import User
        root['m'] = meeting = Meeting()
        root.users['a_user'] = User()
        root.users['b_user'] = User()
        root.users['c_user'] = User()
        meeting.add_groups('a_user', ['role:a'])
        meeting.add_groups('b_user', ['role:a'])
        self.assertEqual(security.find_role_userids(meeting, 'role:a'), frozenset(['a_user', 'b_user']))

    def test_find_role_userids_no_match(self):
        root = self._fixture()
        self.assertEqual(security.find_role_userids(root, 'role:404'), frozenset())
