import unittest

from pyramid import testing
from zope.interface.verify import verifyObject


class UserTagsTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_adapted_obj(self):
        from voteit.core.models.user_tags import UserTags
        from voteit.core.models.base_content import BaseContent
        context = BaseContent()
        return UserTags(context)

    def test_interface(self):
        from voteit.core.models.interfaces import IUserTags
        obj = self._make_adapted_obj()
        self.assertTrue(verifyObject(IUserTags, obj))

    def test_add(self):
        obj = self._make_adapted_obj()
        obj.add('tag', 'BennyBoy')
        self.failUnless('tag' in obj.tags_storage.keys())
        self.failUnless('BennyBoy' in obj.tags_storage['tag'])
        obj.add('hello', 'robin')
        obj.add('hello', 'anders')
        self.assertEqual(set(['tag', 'hello']), set(obj.tags_storage.keys()))
        self.assertEqual(set(['robin', 'anders']), set(obj.tags_storage['hello']))

    def test_add_bad_text_tag(self):
        obj = self._make_adapted_obj()
        self.assertRaises(ValueError, obj.add, 'badness%&', 'BennyBoy')

    def test_add_not_string(self):
        obj = self._make_adapted_obj()
        self.assertRaises(TypeError, obj.add, {}, 'BennyBoy')

    def test_userids_for_tag(self):
        obj = self._make_adapted_obj()
        obj.add('like', 'James')
        obj.add('like', 'Joyce')
        self.assertEqual(set(['James', 'Joyce']), set(obj.userids_for_tag('like')))

    def test_remove(self):
        obj = self._make_adapted_obj()
        obj.add('like', 'James')
        obj.add('like', 'Joyce')
        self.assertEqual(set(['James', 'Joyce']), set(obj.userids_for_tag('like')))
        obj.remove('like', 'Joyce')
        self.assertEqual(set(['James']), set(obj.userids_for_tag('like')))

    def test_registration(self):
        self.config.include('voteit.core.models.user_tags')
        from voteit.core.models.base_content import BaseContent
        context = BaseContent()
        from voteit.core.models.interfaces import IUserTags
        adapter = self.config.registry.queryAdapter(context, IUserTags)
        self.failUnless(IUserTags.providedBy(adapter))
