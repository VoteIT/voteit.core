import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.interface.exceptions import BrokenImplementation
from zope.component import queryUtility


def _bad_mock_plugin_class():
    """ Get a mock plugin class that doesn't provide the proper attributes. """
    from voteit.core.models.poll_plugin import PollPlugin
    class BadPlugin(PollPlugin):
        pass
    return BadPlugin

    
class PollPluginTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _example_plugin_class(self):
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        return MajorityPollPlugin

    def test_register_bad_plugin(self):
        """ Check that registration of a bad plugin raises errors.
        """
        from voteit.core import register_poll_plugin
        bad_cls = _bad_mock_plugin_class()
        
        self.assertRaises(BrokenImplementation, register_poll_plugin, bad_cls)

    def test_good_plugin(self):
        """ Register example plugin that ships with voteit. """ 
        from voteit.core import register_poll_plugin
        from voteit.core.models.interfaces import IPollPlugin
        
        good_cls = self._example_plugin_class()
        register_poll_plugin(good_cls, verify=0)
        name = good_cls.name
        
        util = queryUtility(IPollPlugin, name = name)
        self.failUnless(util)
        self.assertTrue(verifyObject(IPollPlugin, util))
