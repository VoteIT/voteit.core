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

    def _make_schema(self):
        import colander
        class Schema(colander.Schema):
            title = colander.SchemaNode(colander.String())
            number = colander.SchemaNode(colander.Integer())
        return Schema()

    def test_verify_interface(self):
        from voteit.core.models.interfaces import IBaseContent
        obj = self._make_obj()
        self.assertTrue(verifyObject(IBaseContent, obj))
    
    def test_uid_generated(self):
        obj = self._make_obj()
        self.failIf(obj.uid is None)
        self.assertTrue(isinstance(obj.uid, unicode))
    
    def test_uid_compare(self):
        obj1 = self._make_obj()
        obj2 = self._make_obj()
        self.assertNotEqual(obj1, obj2)

    def test_creators(self):
        obj = self._make_obj()
        self.assertEqual(obj.creators, ())
        obj.creators = ['franz']
        self.assertEqual(obj.creators, ('franz',))

    def test_get_set_field_value(self):
        obj = self._make_obj()
        obj.set_field_value('title', "Hello world")
        self.assertEqual(obj.get_field_value('title'), "Hello world")
        
    def test_get_field_appstruct(self):
        obj = self._make_obj()
        obj.set_field_value('title', 'Hello')
        obj.set_field_value('number', 1)
        schema = self._make_schema()
        appstruct = obj.get_field_appstruct(schema)
        self.assertEqual(appstruct, {'title':'Hello', 'number':1})

    def test_get_field_appstruct_nonexistent(self):
        """ Check that appstruct doesn't return a value if nothing exists. """
        obj = self._make_obj()
        obj.set_field_value('title', 'Hello') 
        schema = self._make_schema()
        appstruct = obj.get_field_appstruct(schema)
        self.assertEqual(appstruct, {'title':'Hello'})

    def test_get_field_appstruct_with_none(self):
        """ Check that None is treated as a value. """
        obj = self._make_obj()
        obj.set_field_value('title', None) 
        schema = self._make_schema()
        appstruct = obj.get_field_appstruct(schema)
        self.assertEqual(appstruct, {'title':None})
        
    def test_set_field_appstruct(self):
        obj = self._make_obj()
        appstruct = {'title':'Hello', 'number':2}
        obj.set_field_appstruct(appstruct)
        self.assertEqual(obj.get_field_value('title'), 'Hello')
        self.assertEqual(obj.get_field_value('number'), 2)

    def test_set_restricted_key_with_set_field_appstruct(self):
        obj = self._make_obj()
        appstruct = {'title':'Hello', 'number':2, 'csrf_token':"don't save me"}
        obj.set_field_appstruct(appstruct)
        self.assertEqual(obj.get_field_value('csrf_token'), None)

    def test_set_restricted_key_with_set_field(self):
        obj = self._make_obj()
        obj.set_field_value('csrf_token', "don't save me")
        self.assertEqual(obj.get_field_value('csrf_token'), None)