import unittest

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy

from voteit.core.bootstrap import bootstrap_voteit
from voteit.core import security


class UnreadAwareTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _fixture_and_setup(self):
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')
        self.config.scan('voteit.core.models.site')
        self.config.scan('voteit.core.models.user')
        self.config.scan('voteit.core.models.users')
        self.config.scan('betahaus.pyracont.fields.password')

        root = bootstrap_voteit(echo=False)
        
        return root

    def _make_proposal(self):
        """ Since it also implements UnreadAware and has required security mixin. """
        from voteit.core.models.proposal import Proposal
        return Proposal()

    def _setup_security(self):
        authn_policy = AuthTktAuthenticationPolicy(secret='secret',
                                                   callback=security.groupfinder)
        authz_policy = ACLAuthorizationPolicy()
        self.config.setup_registry(authorization_policy=authz_policy, authentication_policy=authn_policy)

    def test_subscriber_fired_and_added_users(self):
        self._setup_security()
        self.config.scan('voteit.core.subscribers.unread')
        root = self._fixture_and_setup()
        obj = self._make_proposal()
        root['new'] = obj
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin',)))
