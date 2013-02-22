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


class ImmediateAPTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.plugins.immediate_ap import ImmediateAP
        return ImmediateAP        

    def test_verify_class(self):
        self.assertTrue(verifyClass(IAccessPolicy, self._cut))

    def test_verify_object(self):
        self.assertTrue(verifyObject(IAccessPolicy, self._cut(None)))

    def test_integration(self):
        self.config.include('voteit.core.plugins.immediate_ap')
        meeting = _fixture(self.config)
        self.assertTrue(self.config.registry.queryAdapter(meeting, IAccessPolicy, name = 'public'))
