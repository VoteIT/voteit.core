import unittest

from pyramid import testing
from zope.interface.verify import verifyObject


class SiteRootTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.site import SiteRoot
        return SiteRoot()
    
    def _bootstrap_root(self):
        """ Create a default app root"""
        from voteit.core.bootstrap import bootstrap_voteit
        return bootstrap_voteit()

    def test_verify_interface(self):
        from voteit.core.models.interfaces import IBaseContent
        obj = self._make_obj()
        self.assertTrue(verifyObject(IBaseContent, obj))
