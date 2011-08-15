import unittest

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy
from repoze.workflow.workflow import WorkflowError

from voteit.core.bootstrap import bootstrap_voteit
from voteit.core.app import register_content_types
from voteit.core import security


authn_policy = AuthTktAuthenticationPolicy(secret='sosecret',
                                           callback=security.groupfinder)
authz_policy = ACLAuthorizationPolicy()

ALL_TEST_USERS = set(('fredrik', 'anders', 'hanna', 'robin', 'admin'))

class SecurityTests(unittest.TestCase):
    """ Tests for methods in voteit.core.security.
    """
    
    def setUp(self):
        self.config = testing.setUp()
        self.config.setup_registry(authentication_policy=authn_policy,
                                   authorization_policy=authz_policy)
        ct = """
    voteit.core.models.site
    voteit.core.models.user
    voteit.core.models.users
        """
        self.config.registry.settings['content_types'] = ct #Needed for bootstrap_voteit
        register_content_types(self.config)
        self.root = self._fixture()

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        root = bootstrap_voteit(registry=self.config.registry, echo=False)
        from voteit.core.models.user import User
        
        for userid in ('fredrik', 'anders', 'hanna', 'robin'):
            root.users[userid] = User()

        return root

    def test_find_authorized_userids_admin(self):
        res = security.find_authorized_userids(self.root, (security.ROLE_ADMIN,))
        self.assertEqual(res, set(('admin',)))
    
    def test_find_aithorized_userids_several_perms(self):
        self.root.add_groups('robin', ('role:Admin',))
        res = security.find_authorized_userids(self.root, (security.VIEW, security.ROLE_ADMIN))
        self.assertEqual(res, set(('admin', 'robin')))

    def test_context_effective_principals_admin(self):
        res = security.context_effective_principals(self.root, 'admin')
        self.assertEqual(res, ['system.Everyone', 'system.Authenticated', 'admin', 'role:Admin'])
        
    def test_context_effective_principals_normal_user(self):
        res = security.context_effective_principals(self.root, 'hanna')
        self.assertEqual(res, ['system.Everyone', 'system.Authenticated', 'hanna'])
    
    def test_groups_added_to_principals(self):
        self.root.add_groups('fredrik', ('group:developer', 'group:Betahaus',))
        res = security.context_effective_principals(self.root, 'fredrik')
        self.assertEqual(res, ['system.Everyone', 'system.Authenticated',
                               'fredrik', 'group:Betahaus', 'group:developer'])

    def test_roles_added_to_principals(self):
        self.root.add_groups('robin', ('role:Admin',))
        res = security.context_effective_principals(self.root, 'robin')
        self.assertEqual(res, ['system.Everyone', 'system.Authenticated',
                               'robin', 'role:Admin'])
    
    def test_unrestricted_wf_transition_to(self):
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml') #Load workflows
        
        from voteit.core.models.meeting import Meeting
        request = testing.DummyRequest()
        obj = Meeting()
        
        #Regular wf method doesn't work
        self.assertRaises(WorkflowError, obj.set_workflow_state, request, 'active')
        
        #But unrestricted does
        security.unrestricted_wf_transition_to(obj, 'active')
        self.assertEqual(obj.get_workflow_state(), 'active')
