import unittest

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from fanstatic import get_needed
from fanstatic import init_needed

from voteit.core.models.interfaces import IFanstaticResources


class FanstaticResourcesTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.fanstatic_resources import FanstaticResources
        return FanstaticResources

    @property
    def _js_resource(self):
        """ This is a real resource.
            It's not relevant what it is for this test, so just change
            resource to point to something else if moved.
        """
        from voteit.core.fanstaticlib import voteit_main_css
        return voteit_main_css
        
    def test_verify_class(self):
        self.assertTrue(verifyClass(IFanstaticResources, self._cut))

    def test_verify_obj(self):
        self.assertTrue(verifyObject(IFanstaticResources, self._cut()))

    def test_integration(self):
        self.config.include('voteit.core.models.fanstatic_resources')
        self.failUnless(self.config.registry.queryUtility(IFanstaticResources))

    def test_add(self):
        obj = self._cut()
        obj.add('dummy', self._js_resource, discriminator_false)
        self.assertEqual(obj.order, ['dummy'])
        self.assertEqual(obj.resources['dummy'], self._js_resource)
        self.assertEqual(obj.discriminators['dummy'], discriminator_false)

    def test_add_bad_type(self):
        obj = self._cut()
        self.assertRaises(TypeError, obj.add, 'dummy', 'badness')

    def test_add_bad_discriminator(self):
        obj = self._cut()
        self.assertRaises(TypeError, obj.add, 'dummy', self._js_resource, 'badness')

    def test_include_needed(self):
        init_needed()
        obj = self._cut()
        obj.add('true', self._js_resource, discriminator_true)
        obj.add('false', self._js_resource, discriminator_false)
        obj.add('none', self._js_resource)
        self.assertEqual(obj.include_needed(None, None, None), ['true', 'none'])
        needed = get_needed().resources()
        self.assertIn(self._js_resource, needed)

    def test_order(self):
        obj = self._cut()
        obj.add('1', self._js_resource)
        obj.add('2', self._js_resource)
        obj.add('3', self._js_resource)
        obj.order = ['1', '3', '2']
        self.assertEqual(obj.include_needed(None, None, None), ['1', '3', '2'])    


def discriminator_false(*args):
    return False

def discriminator_true(*args):
    return True
