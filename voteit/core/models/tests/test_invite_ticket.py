import unittest
from datetime import datetime

from pyramid import testing
from zope.interface.verify import verifyObject, verifyClass
from pyramid_mailer import get_mailer
from pyramid.exceptions import Forbidden


class InviteTicketTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    @property
    def _get_class(self):
        from voteit.core.models.invite_ticket import InviteTicket
        return InviteTicket
    
    def _make_obj(self):
        return self._get_class('this@email.com', ['role:Moderator'], 'Welcome to the meeting!')
    
    def _make_meeting(self):
        from voteit.core.models.meeting import Meeting
        return Meeting()
    

    def test_verify_interface(self):
        from voteit.core.models.interfaces import IInviteTicket
        self.assertTrue(verifyClass(IInviteTicket, self._get_class))

    def test_send_message_sent(self):
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
        meeting = self._make_meeting()
        obj = self._make_obj()
        
        request = testing.DummyRequest()
        meeting.add_invite_ticket(obj, request)
        ticket = meeting.invite_tickets['this@email.com']
        
        self.assertRaises(Forbidden, ticket.claim, request)

