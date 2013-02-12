import unittest

from pyramid import testing
from pyramid_mailer import get_mailer

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_catalog


class TicketViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.ticket import TicketView
        return TicketView

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        root.users['dummy'] = User()
        return meeting

    def _load_vcs(self):
        self.config.scan('voteit.core.views.components.main')

    def test_claim_ticket(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertIn('form', response)

    def test_claim_ticket_not_logged_in(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(permissive=False)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertEqual(response.location, 'http://example.com/login?came_from=http%3A//example.com')

    def test_claim_ticket_post(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        from voteit.core.models.invite_ticket import InviteTicket
        ticket = InviteTicket('dummy@test.com', ['role:Moderator'], 'Welcome to the meeting!')
        ticket.__parent__ = context
        context.invite_tickets['dummy@test.com'] = ticket
        params = {'add': 'add', 'email': ticket.email, 'token': ticket.token}
        request = testing.DummyRequest(params=params, post=params)
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertEqual(response.location, 'http://example.com/m/')

    def test_claim_ticket_validation_error(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(params={'email': 'dummy@test.com', 'token': 'dummy_token'})
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertIn('form', response)

    def test_claim_ticket_get(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        from voteit.core.models.invite_ticket import InviteTicket
        ticket = InviteTicket('dummy@test.com', ['role:Moderator'], 'Welcome to the meeting!')
        ticket.__parent__ = context
        ticket.token = 'dummy_token'
        context.invite_tickets['dummy@test.com'] = ticket
        params = {'add': 'add', 'email': ticket.email, 'token': ticket.token}
        request = testing.DummyRequest(params=params)
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertEqual(response.location, 'http://example.com/m/')

    def test_claim_ticket_cancel(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertEqual(response.location, 'http://example.com/')

    def test_add_tickets(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.email')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.add_tickets()
        self.assertIn('form', response)

    def test_add_tickets_cancel(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.add_tickets()
        self.assertEqual(response.location, 'http://example.com/m/')

    def test_add_tickets_post(self):
        self.config.scan('voteit.core.models.invite_ticket')
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post = {'add': 'add', 
                                               'emails': 'dummy1@test.com\ndummy1@test.com', 
                                               'message': 'Welcome to the meeting!', 
                                               'roles': ['role:Moderator']})
        obj = self._cut(context, request)
        response = obj.add_tickets()
        self.assertEqual(response.location, 'http://example.com/m/')

    def test_add_tickets_post_validation_error(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post = {'add': 'add', 
                                               'emails': '', 
                                               'message': 'Welcome to the meeting!', 
                                               'roles': ['role:Moderator']})
        obj = self._cut(context, request)
        response = obj.add_tickets()
        self.assertIn('form', response)
        
    def test_manage_tickets(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.manage_tickets()
        self.assertIn('form', response)
        
    def test_manage_tickets_cancel(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.manage_tickets()
        self.assertEqual(response.location, 'http://example.com/m/')

    def test_manage_tickets_validation_error(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post = {'resend': 'resend', 
                                               'emails': (),})
        obj = self._cut(context, request)
        response = obj.manage_tickets()
        self.assertIn('form', response)

    def test_manage_tickets_resend(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post = {'resend': 'resend', 
                                               'emails': ['dummy@test.com'],})
        from voteit.core.models.invite_ticket import InviteTicket
        ticket = InviteTicket('dummy@test.com', ['role:Moderator'], 'Welcome to the meeting!')
        ticket.__parent__ = context
        context.invite_tickets['dummy@test.com'] = ticket
        obj = self._cut(context, request)
        response = obj.manage_tickets()
        self.assertEqual(response.location, 'http://example.com/m/')
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        
    def test_manage_tickets_delete(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post = {'delete': 'delete', 
                                               'emails': ['dummy@test.com'],})
        from voteit.core.models.invite_ticket import InviteTicket
        ticket = InviteTicket('dummy@test.com', ['role:Moderator'], 'Welcome to the meeting!')
        ticket.__parent__ = context
        context.invite_tickets['dummy@test.com'] = ticket
        obj = self._cut(context, request)
        response = obj.manage_tickets()
        self.assertEqual(response.location, 'http://example.com/m/')
        self.assertNotIn('dummy@test.com', context.invite_tickets)
