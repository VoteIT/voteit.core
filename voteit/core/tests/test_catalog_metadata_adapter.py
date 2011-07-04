import unittest
from datetime import datetime

from pyramid import testing
from pyramid.traversal import resource_path
from zope.interface import implements

from voteit.core.models.interfaces import ICatalogMetadataEnabled
from voteit.core.models.site import SiteRoot


class DummyMetadataContext(object):
    implements(ICatalogMetadataEnabled)
    __name__ = 'dummy' #Path will be same for all dummies
    
    def __init__(self):
        self.title = u"Hello world"
        self.created = datetime.now()
        

class CatalogMetadataTests(unittest.TestCase):
    """ Testcase for CatalogMetadata adapter. The adapter is also covered in the catalog tests.
    """
    def setUp(self):
        self.config = testing.setUp()
        self.root = SiteRoot() #Contains a catalog

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self, context):
        from voteit.core.models.catalog import CatalogMetadata
        return CatalogMetadata(context)
    
    def test_add_and_get_metadata(self):
        context = DummyMetadataContext()
        obj = self._make_obj(context)
        
        dm = self.root.catalog.document_map
        
        doc_id = dm.add(resource_path(context))
        dm.add_metadata(doc_id, obj())
        
        metadata = dm.get_metadata(doc_id)
        self.assertEqual(metadata['title'], context.title)
        self.assertEqual(metadata['created'], context.created)
        
    def test_returned_metadata(self):
        context = DummyMetadataContext()
        obj = self._make_obj(context)
        result = obj()
        
        self.assertEqual(result['title'], context.title)
        self.assertEqual(result['created'], context.created)
        