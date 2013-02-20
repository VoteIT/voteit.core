import unittest

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.testing_helpers import bootstrap_and_fixture


def _fixture(config):
    root = bootstrap_and_fixture(config)
    from voteit.core.models.meeting import Meeting
    root['m'] = Meeting()
    return root['m']


class InviteOnlyAPTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.plugins.invite_only_ap import InviteOnlyAP
        return InviteOnlyAP        

    def test_verify_class(self):
        self.assertTrue(verifyClass(IAccessPolicy, self._cut))

    def test_verify_object(self):
        self.assertTrue(verifyObject(IAccessPolicy, self._cut(None)))

    def test_integration(self):
        self.config.include('voteit.core.plugins.invite_only_ap')
        meeting = _fixture(self.config)
        self.assertTrue(self.config.registry.queryAdapter(meeting, IAccessPolicy, name = 'invite_only'))
