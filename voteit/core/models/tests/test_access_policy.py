import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.interface.verify import verifyClass

from voteit.core.models.interfaces import IAccessPolicy


class AccessPolicyTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.access_policy import AccessPolicy
        return AccessPolicy

    @property
    def _meeting(self):
        from voteit.core.models.meeting import Meeting
        return Meeting

    def test_verify_class(self):
        self.failUnless(verifyClass(IAccessPolicy, self._cut))

    def test_verify_obj(self):
        m = self._meeting()
        self.failUnless(verifyObject(IAccessPolicy, self._cut(m)))
