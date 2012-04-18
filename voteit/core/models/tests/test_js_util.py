import unittest

from pyramid import testing
from pyramid.i18n import TranslationString
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core.models.interfaces import IJSUtil


class JSUtilTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.js_util import JSUtil
        return JSUtil

    def test_verify_class(self):
        self.assertTrue(verifyClass(IJSUtil, self._cut))

    def test_verify_obj(self):
        self.assertTrue(verifyObject(IJSUtil, self._cut()))

    def test_add_translations(self):
        ts1 = TranslationString('first', domain = 'hello')
        ts2 = TranslationString('second', domain = 'world')
        obj = self._cut()
        obj.add_translations(ts1, ts2)
        self.assertIn('first', obj.translations)
        self.assertIn('second', obj.translations)

    def test_add_translations_wrong_type(self):
        obj = self._cut()
        self.assertRaises(TypeError, obj.add_translations, "hello")

    def test_add_translations_bad_msgid(self):
        ts = TranslationString('bad&msgid! !"', domain = 'hello')
        obj = self._cut()
        self.assertRaises(ValueError, obj.add_translations, ts)

    def test_add_translations_no_domain(self):
        ts = TranslationString('no_domain_added')
        obj = self._cut()
        self.assertRaises(ValueError, obj.add_translations, ts)

    def test_get_translations(self):
        ts1 = TranslationString('first', domain = 'hello')
        ts2 = TranslationString('second', domain = 'world')
        obj = self._cut()
        obj.add_translations(ts1, ts2)
        res = obj.get_translations()
        self.assertIn('first', res)
        self.assertIn('second', res)
        self.assertEqual(res['first'], ts1)

    def test_get_translations_returns_copy(self):
        obj = self._cut()
        self.assertIsNot(obj.translations, obj.get_translations())

    def test_integration(self):
        self.config.include('voteit.core.models.js_util')
        self.failUnless(self.config.registry.queryUtility(IJSUtil))
