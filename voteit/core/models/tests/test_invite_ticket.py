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
        self.config.include('pyramid_chameleon')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        self.config.scan('voteit.core.models.invite_ticket')
        meeting = _fixture(self.config)['m']
        request = testing.DummyRequest()
        obj = meeting.add_invite_ticket('me@home.com', [security.ROLE_MODERATOR, security.ROLE_DISCUSS], sent_by = 'admin')
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 0)
        #Send
        obj.send(request)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(len(obj.sent_dates), 1)
        
    def test_claim_ticket(self):
        self.config.scan('voteit.core.views.components.email')
        self.config.scan('voteit.core.models.invite_ticket')
        meeting = _fixture(self.config)['m']
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)
        obj = meeting.add_invite_ticket('this@email.com', [security.ROLE_MODERATOR, security.ROLE_DISCUSS])
        request = testing.DummyRequest()
        obj.claim(request)
        self.assertTrue(isinstance(obj.closed, datetime))
        self.assertEqual(obj.claimed_by, 'some_user')
        self.assertEqual(obj.get_workflow_state(), 'closed')
        self.assertEqual(meeting.get_groups('some_user'), (security.ROLE_MODERATOR, security.ROLE_DISCUSS, security.ROLE_VIEWER))

    def test_claim_closed(self):
        self.config.scan('voteit.core.views.components.email')
        self.config.scan('voteit.core.models.invite_ticket')
        meeting = _fixture(self.config)['m']
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)
        request = testing.DummyRequest()
        obj = meeting.add_invite_ticket('this@email.com', [security.ROLE_PROPOSE])
        #Set ticket to closed
        obj.set_workflow_state(request, 'closed')
        self.assertRaises(Forbidden, obj.claim, request)

    def test_claim_unathenticated(self):
        self.config.scan('voteit.core.views.components.email')
        self.config.scan('voteit.core.models.invite_ticket')
        meeting = _fixture(self.config)['m']
        request = testing.DummyRequest()
        obj = meeting.add_invite_ticket('this@email.com', [security.ROLE_PROPOSE])
        self.assertRaises(Forbidden, obj.claim, request)

    def test_force_selectable_roles(self):
        self.assertRaises(ValueError, self._cut, 'hello@world.com', 'bad_role', "This won't work")

    def test_force_lowercase(self):
        obj = self._cut('HELLO@WORLD.com', [security.ROLE_DISCUSS])
        self.assertEqual(obj.email, 'hello@world.com')


def _fixture(config):
    from voteit.core.models.meeting import Meeting
    root = bootstrap_and_fixture(config)
    root['m'] = Meeting()
    return root
