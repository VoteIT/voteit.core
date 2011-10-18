import unittest

from pyramid import testing
from pyramid.threadlocal import get_current_registry
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from zope.interface.exceptions import BrokenImplementation
from zope.interface.exceptions import BrokenMethodImplementation
from zope.interface.exceptions import DoesNotImplement
from zope.component import queryUtility
from zope.interface import implements

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

    def _example_plugin_class(self):
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        return MajorityPollPlugin
    
    def _bad_method_plugin(self):
        class _BadMethodPlugin(self._cut):
            def get_vote_schema(self, to, many, arguments):
                pass
        return _BadMethodPlugin

    def test_verify_class(self):
        self.failUnless(verifyClass(IPollPlugin, self._cut))

    def test_verify_obj(self):
        context = testing.DummyModel()
        self.failUnless(verifyObject(IPollPlugin, self._cut(context)))

    def test_register_bad_method_plugin(self):
        from voteit.core.app import register_poll_plugin
        self.assertRaises(BrokenMethodImplementation, register_poll_plugin, self._bad_method_plugin())

    def test_register_bad_plugin_not_implemented(self):
        from voteit.core.app import register_poll_plugin
        self.assertRaises(DoesNotImplement, register_poll_plugin, object)

    def test_register_bad_plugin_wrong_attrs(self):
        from voteit.core.app import register_poll_plugin
        class _BadPlugin(object):
            implements(IPollPlugin)
        self.assertRaises(BrokenImplementation, register_poll_plugin, _BadPlugin)

    def test_good_plugin(self):
        """ Register example plugin that ships with voteit. """ 
        from voteit.core.app import register_poll_plugin
        from voteit.core.models.poll import Poll
        
        registry = get_current_registry()
        good_cls = self._example_plugin_class()
        register_poll_plugin(good_cls, verify=0, registry=registry)
        name = good_cls.name
        poll = Poll()
        poll_plugin = registry.getAdapter(poll, name = name, interface = IPollPlugin)
        self.failUnless( verifyObject(IPollPlugin, poll_plugin) )
