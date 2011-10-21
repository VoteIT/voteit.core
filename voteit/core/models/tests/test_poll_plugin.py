import unittest

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core.models.interfaces import IPollPlugin

    
class PollPluginTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.poll_plugin import PollPlugin
        return PollPlugin

    def test_verify_class(self):
        self.failUnless(verifyClass(IPollPlugin, self._cut))

    def test_verify_obj(self):
        context = testing.DummyModel()
        self.failUnless(verifyObject(IPollPlugin, self._cut(context)))
