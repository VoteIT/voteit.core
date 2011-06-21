import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.component.event import objectEventNotify

from voteit.core.app import register_content_types
from voteit.core.bootstrap import bootstrap_voteit
from voteit.core.models.interfaces import IContentUtility
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core.events import ObjectUpdatedEvent
from voteit.core.testing import testing_sql_session


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        ct = """
    voteit.core.models.meeting
    voteit.core.models.site
    voteit.core.models.user
    voteit.core.models.users
        """
        self.config.registry.settings['content_types'] = ct
        register_content_types(self.config)

        testing_sql_session(self.config) #To register session utility   
        self.config.scan('voteit.core.subscribers.catalog')

        self.root = bootstrap_voteit(registry=self.config.registry, echo=False)
        self.content_types = self.config.registry.getUtility(IContentUtility)
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    def test_indexed_on_add(self):
        title_index = self.root.catalog['title']
        title_count = title_index.documentCount()
        meeting = self.content_types['Meeting'].type_class()
        meeting.title = 'hello world'
        
        self.root['meeting'] = meeting
        
        self.assertEqual(title_index.documentCount(), title_count + 1)

    def test_unindexed_on_remove(self):
        title_index = self.root.catalog['title']
        title_count = title_index.documentCount()

        meeting = self.content_types['Meeting'].type_class()
        meeting.title = 'hello world'
        
        self.root['meeting'] = meeting
        
        self.assertEqual(title_index.documentCount(), title_count + 1)
        
        del self.root['meeting']
        self.assertEqual(title_index.documentCount(), title_count)
        
    def test_reindexed_on_update(self):
        meeting = self.content_types['Meeting'].type_class()
        meeting.title = 'hello world'
        self.root['meeting'] = meeting
        
        query = self.root.catalog.query
        self.assertEqual(query("title == 'hello world'")[0], 1)
        
        self.root['meeting'].title = 'me and my little friends'
        #We'll have to kick the subscriber manually
        objectEventNotify(ObjectUpdatedEvent(self.root['meeting']))
        
        self.assertEqual(query("title == 'hello world'")[0], 0)
        self.assertEqual(query("title == 'me and my little friends'")[0], 1)
        
