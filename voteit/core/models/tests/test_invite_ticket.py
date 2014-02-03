import unittest
from datetime import datetime

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from pyramid_mailer import get_mailer
from pyramid.exceptions import Forbidden

from voteit.core.models.interfaces import IInviteTicket
from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core import security


class InviteTicketTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.invite_ticket import InviteTicket
        return InviteTicket

    def test_verify_class(self):
        self.assertTrue(verifyClass(IInviteTicket, self._cut))

    def test_verify_obj(self):
        self.assertTrue(verifyObject(IInviteTicket, self._cut('me@home.com', [security.ROLE_MODERATOR])))

    def test_send_message_sent(self):
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        meeting = _fixture(self.config)['m']
        obj = self._cut('me@home.com', [security.ROLE_MODERATOR, security.ROLE_DISCUSS], sent_by = 'admin')
        request = testing.DummyRequest()
        #This method calls send on the ticket
        meeting.add_invite_ticket(obj, request)
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        #Resend
        obj.send(request)
        self.assertEqual(len(mailer.outbox), 2)
        self.assertEqual(len(obj.sent_dates), 2)
        
    def test_claim_ticket(self):
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        meeting = _fixture(self.config)['m']
        obj = self._cut('this@email.com', [security.ROLE_MODERATOR, security.ROLE_DISCUSS])
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)
        request = testing.DummyRequest()
        meeting.add_invite_ticket(obj, request)
        ticket = meeting.invite_tickets['this@email.com']
        ticket.claim(request)
        self.assertTrue(isinstance(ticket.closed, datetime))
        self.assertEqual(ticket.claimed_by, 'some_user')
        self.assertEqual(ticket.get_workflow_state(), 'closed')
        self.assertEqual(meeting.get_groups('some_user'), (security.ROLE_MODERATOR, security.ROLE_DISCUSS, security.ROLE_VIEWER))

    def test_claim_closed(self):
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        meeting = _fixture(self.config)['m']
        obj = self._cut('this@email.com', [security.ROLE_PROPOSE])
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)
        request = testing.DummyRequest()
        meeting.add_invite_ticket(obj, request)
        ticket = meeting.invite_tickets['this@email.com']
        #Set ticket to closed
        ticket.set_workflow_state(request, 'closed')
        self.assertRaises(Forbidden, ticket.claim, request)

    def test_claim_unathenticated(self):
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        meeting = _fixture(self.config)['m']
        obj = self._cut('this@email.com', [security.ROLE_PROPOSE])        
        request = testing.DummyRequest()
        meeting.add_invite_ticket(obj, request)
        ticket = meeting.invite_tickets['this@email.com']
        self.assertRaises(Forbidden, ticket.claim, request)

    def test_force_selectable_roles(self):
        self.assertRaises(ValueError, self._cut, 'hello@world.com', 'bad_role', "This won't work")

    def test_add_invite_ticket_traversal(self):
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        request = testing.DummyRequest()
        meeting = _fixture(self.config)['m']
        obj = self._cut('this@email.com', [security.ROLE_PROPOSE])        
        meeting.add_invite_ticket(obj, request)
        self.assertEqual(meeting, obj.__parent__)


def _fixture(config):
    from voteit.core.models.meeting import Meeting
    root = bootstrap_and_fixture(config)
    root['m'] = Meeting()
    return root
