import unittest
import os

from pyramid import testing
from zope.interface.verify import verifyObject


here = os.path.abspath(os.path.dirname(__file__))
html_file_path = os.path.join(here, 'fixture', 'text.html')


class HelpUtilTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.help_util import HelpUtil
        return HelpUtil()

    def test_verify_interface(self):
        from voteit.core.models.interfaces import IHelpUtil
        obj = self._make_obj()
        self.assertTrue(verifyObject(IHelpUtil, obj))

    def test_add_method(self):
        from voteit.core.app import add_help_util
        from voteit.core.models.interfaces import IHelpUtil
        
        add_help_util(self.config, locale='sv')
        util = self.config.registry.queryUtility(IHelpUtil)
        
        self.failUnless(util)
    
    def test_set_default_locale(self):
        obj = self._make_obj()
        obj.set_default_locale('lang')
        self.assertEqual(obj.locale, 'lang')

    def test_add_help_text(self):
        obj = self._make_obj()
        obj.add_help_text('Dummy', 'Hello default!')
        obj.add_help_text('Dummy', 'Hello!', locale='test')
        self.assertEqual(obj.get('Dummy'), 'Hello default!')
        self.assertEqual(obj.get('Dummy', locale='test'), 'Hello!')
        
    def test_add_help_file(self):
        obj = self._make_obj()
        obj.add_help_file('Dummy', html_file_path)
        obj.add_help_file('Dummy', html_file_path, locale='test')
        
        self.assertEqual(obj.get('Dummy'), '<div>Some text!</div>')
        self.assertEqual(obj.get('Dummy', locale='test'), '<div>Some text!</div>')

    def test_add_help_file_file_not_found(self):
        obj = self._make_obj()
        self.assertRaises(IOError, obj.add_help_file, 'Buhu', './404_i_dont_exist')

    def test_get(self):
        obj = self._make_obj()
        obj.set_default_locale('first')
        obj.add_help_text('one', 'one text', locale='first')
        obj.add_help_text('two', 'two texts', locale='second')
        obj.add_help_text('three', 'three texts', locale='third')
        
        self.assertEqual(obj.get('one'), 'one text')
        self.assertEqual(obj.get('one', 'first'), 'one text')
        self.assertEqual(obj.get('two'), None)
        self.assertEqual(obj.get('two', 'second'), 'two texts')
        self.assertEqual(obj.get('two', 'first'), None)
        self.assertEqual(obj.get('three', 'third'), 'three texts')
        self.assertEqual(obj.get('404'), None)
        self.assertEqual(obj.get('404', '404'), None)
        