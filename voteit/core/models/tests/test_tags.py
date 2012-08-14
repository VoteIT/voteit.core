import unittest

from pyramid import testing
from zope.interface.verify import verifyObject


class UserTagsTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.tags import Tags
        return Tags()

    def test_interface(self):
        from voteit.core.models.interfaces import ITags
        obj = self._make_obj()
        self.assertTrue(verifyObject(ITags, obj))

    def test__find_tags(self):
        obj = self._make_obj()
        obj._find_tags('#Quisque #aliquam,#ante in #tincidunt #aliquam. #Risus neque#eleifend #nunc')
        self.assertIn('Quisque', obj.tags)
        self.assertIn('aliquam', obj.tags)
        self.assertIn('ante', obj.tags)
        self.assertIn('tincidunt', obj.tags)
        self.assertIn('aliquam', obj.tags)
        self.assertIn('Risus', obj.tags)
        self.assertIn('nunc', obj.tags)
        self.assertNotIn('eleifend', obj.tags)