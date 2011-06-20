import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.interface.exceptions import BrokenImplementation
from zope.interface.exceptions import DoesNotImplement
from zope.component import queryUtility
from pyramid.threadlocal import get_current_registry


class ContentUtilityTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _make_obj(self):
        from voteit.core.models.content_utility import ContentUtility
        return ContentUtility()

    def _register_util(self, registry):
        from voteit.core.models.interfaces import IContentUtility
        obj = self._make_obj()
        registry.registerUtility(obj, IContentUtility)

    def _make_content_type_info(self):
        from voteit.core.models.meeting import Meeting, construct_schema
        from voteit.core.models.content_type_info import ContentTypeInfo
        return ContentTypeInfo(construct_schema, Meeting)

    def test_verify_obj(self):
        from voteit.core.models.interfaces import IContentUtility
        obj = self._make_obj()
        self.assertTrue(verifyObject(IContentUtility, obj))

    def test_add_good(self):
        obj = self._make_obj()
        cti = self._make_content_type_info()
        obj.add(cti)
        
        self.failUnless(u'Meeting' in obj)

    def test_add_bad(self):
        obj = self._make_obj()
        cti = object()
        
        self.assertRaises(DoesNotImplement, obj.add, cti)

    def test_create(self):
        from voteit.core.models.meeting import Meeting, construct_schema
        from voteit.core.models.interfaces import IContentTypeInfo
        util = self._make_obj()
        cti = util.create(construct_schema, Meeting)

        self.assertTrue(verifyObject(IContentTypeInfo, cti))

    def test_addable_in_type(self):
        """ Add meeting to util and test that it's addable in the site root. """
        obj = self._make_obj()
        cti = self._make_content_type_info()
        obj.add(cti)
        
        self.assertEqual(len(obj.addable_in_type('SiteRoot')), 1)
        self.assertEqual(len(obj.addable_in_type('Type 404')), 0)
        

    def test_register_content_info_bad(self):
        """ Check that registration of a bad plugin raises errors.
            Using register_content_info
        """
        from voteit.core.app import register_content_info

        class BadCls(object):
            pass

        registry = get_current_registry() #To speed up the test, since we need it later
        self._register_util(registry) #Add utility
        
        self.assertRaises(BrokenImplementation, register_content_info, None, BadCls, registry=registry)

    def test_register_content_info_good(self):
        """ Register meeting as a content type. Should work as expected unless the meeting tests fail :)
        """
        from voteit.core.models.interfaces import IContentUtility
        from voteit.core.app import register_content_info
        from voteit.core.models.meeting import Meeting, construct_schema
        
        registry = get_current_registry() #To speed up the test, since we need it later
        self._register_util(registry) #Add utility
        register_content_info(construct_schema, Meeting, verify=False, registry=registry)
        
        util = registry.getUtility(IContentUtility)
        
        self.failUnless(u'Meeting' in util)
