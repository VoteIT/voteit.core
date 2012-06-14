import unittest
from datetime import datetime

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from pyramid_mailer import get_mailer
from pyramid.exceptions import Forbidden

from voteit.core.models.interfaces import IInviteTicket


class InviteTicketTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.invite_ticket import InviteTicket
        return InviteTicket
    
    def _make_obj(self):
        return self._cut('this@email.com', ['role:Moderator'], 'Welcome to the meeting!')
    
    def _make_meeting(self):
        from voteit.core.models.meeting import Meeting
        return Meeting()

    def test_verify_class(self):
        self.assertTrue(verifyClass(IInviteTicket, self._cut))

    def test_verify_obj(self):
        self.assertTrue(verifyObject(IInviteTicket, self._make_obj()))

    def test_send_message_sent(self):
        self.config.scan('voteit.core.views.components.email')
        meeting = self._make_meeting()
        obj = self._make_obj()
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
        meeting = self._make_meeting()
        obj = self._make_obj()
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)
        request = testing.DummyRequest()
        
        meeting.add_invite_ticket(obj, request)

        ticket = meeting.invite_tickets['this@email.com']
        ticket.claim(request)
        
        self.assertTrue(isinstance(ticket.closed, datetime))
        self.assertEqual(ticket.claimed_by, 'some_user')
        self.assertEqual(ticket.get_workflow_state(), 'closed')
        self.assertEqual(meeting.get_groups('some_user'), ('role:Moderator',))

    def test_claim_closed(self):
        self.config.scan('voteit.core.views.components.email')
        meeting = self._make_meeting()
        obj = self._make_obj()
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
        meeting = self._make_meeting()
        obj = self._make_obj()
        
        request = testing.DummyRequest()
        meeting.add_invite_ticket(obj, request)
        ticket = meeting.invite_tickets['this@email.com']
        
        self.assertRaises(Forbidden, ticket.claim, request)

    def test_force_selectable_roles(self):
        self.assertRaises(ValueError, self._cut, 'hello@world.com', 'bad_role', "This won't work")
