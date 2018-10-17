from unittest import TestCase

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core import security


class AutoClaimTicketTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        self.config.include('voteit.core.testing_helpers.register_catalog')
        root = bootstrap_and_fixture(self.config)
        self.config.include('voteit.core.models.invite_ticket')
        root['m'] = Meeting()
        root['users']['admin'].email = 'tester@voteit.se'
        return root

    def test_auto_claim_on_add_user(self):
        root = self._fixture()
        self.config.include('voteit.core.subscribers.auto_claim_ticket')
        self.config.include('arche.subscribers')  #<- Delegating subscriber here
        request = testing.DummyRequest()
        self.config.begin(request)
        root['m'].add_invite_ticket('other@voteit.se', roles = [security.ROLE_VIEWER])
        from voteit.core.models.user import User
        user = User(email = 'other@voteit.se', email_validated = True)
        root['users']['tester'] = user
        self.assertIn(security.ROLE_VIEWER, root['m'].local_roles['tester'])        

    def test_auto_claim_on_validated(self):        
        root = self._fixture()
        self.config.include('voteit.core.subscribers.auto_claim_ticket')
        request = testing.DummyRequest()
        self.config.begin(request)
        root['m'].add_invite_ticket('tester@voteit.se', roles = [security.ROLE_VIEWER])
        root['users']['admin'].email_validated = True
        self.assertIn(security.ROLE_VIEWER, root['m'].local_roles['admin'])        
