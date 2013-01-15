# -*- coding: utf-8 -*-

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

    def test_find_tags(self):
        obj = self._make_obj()
        res = obj.find_tags(u"#Quisque #aliquam,#ante in #tincidunt #Äliqöåm. #Risus neque#eleifend #nunc&#34;")
        self.assertIn('quisque', res)
        self.assertIn('aliquam', res)
        self.assertIn('ante', res)
        self.assertIn('tincidunt', res)
        self.assertIn(u'äliqöåm', res)
        self.assertIn('risus', res)
        self.assertIn('nunc', res)
        self.assertNotIn('eleifend', res)
        self.assertNotIn('34', res)

    def test_add_tags(self):
        obj = self._make_obj()
        obj.add_tags('Quisque aliquam ante')
        self.assertIn('quisque', obj._tags)
        self.assertIn('aliquam', obj._tags)
        self.assertIn('ante', obj._tags)
        
    def test_remove_tags(self):
        obj = self._make_obj()
        obj.add_tags('Quisque')
        self.assertIn('quisque', obj._tags)
        obj.remove_tags('Quisque')
        self.assertNotIn('Quisque', obj._tags)
        self.assertNotIn('quisque', obj._tags)

    def test_set_tags(self):
        obj = self._make_obj()
        obj.add_tags('Quisque')
        self.assertIn('quisque', obj._tags)
        obj.set_tags('hello WORLD')
        self.assertEqual(set(obj._tags), set(['hello', 'world']))
