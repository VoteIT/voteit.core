import unittest

from pyramid import testing
from zope.interface.verify import verifyObject


class BaseContentTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.base_content import BaseContent
        return BaseContent()

    def test_verify_interface(self):
        from voteit.core.models.interfaces import IBaseContent
        obj = self._make_obj()
        self.assertTrue(verifyObject(IBaseContent, obj))
    
    def test_uid_generated(self):
        obj = self._make_obj()
        self.failIf(obj.uid is None)
    
    def test_uid_compare(self):
        obj1 = self._make_obj()
        obj2 = self._make_obj()
        self.assertNotEqual(obj1, obj2)