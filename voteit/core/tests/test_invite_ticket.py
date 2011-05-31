import unittest

from pyramid import testing
from zope.interface.verify import verifyObject, verifyClass


class InviteTicketTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _get_class(self):
        from voteit.core.models.invite_ticket import InviteTicket
        return InviteTicket

    def test_verify_interface(self):
        from voteit.core.models.interfaces import IInviteTicket
        self.assertTrue(verifyClass(IInviteTicket, self._get_class))

    #FIXME: Proper testing of claim functionality etc