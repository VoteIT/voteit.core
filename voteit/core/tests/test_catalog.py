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
from voteit.core.security import ROLE_OWNER


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

class CatalogIndexTests(unittest.TestCase):
    """ Make sure indexes work as expected. """
    
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
        self.query = self.root.catalog.query

    def tearDown(self):
        testing.tearDown()
    
    def _add_mock_meeting(self):
        obj = self.content_types['Meeting'].type_class()
        obj.title = 'Testing catalog'
        obj.uid = 'simple_uid'
        obj.creators = ['demo_userid']
        obj.add_groups('demo_userid', (ROLE_OWNER,))
        self.root['meeting'] = obj
        return obj

    def test_title(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("title == 'Testing catalog'")[0], 1)
    
    def test_sortable_title(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("sortable_title == 'testing catalog'")[0], 1)

    def test_uid(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("uid == 'simple_uid'")[0], 1)

    def test_content_type(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("content_type == 'Meeting'")[0], 1)

    def test_workflow_state(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("workflow_state == 'private'")[0], 1)

    def test_path(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("path == '/meeting'")[0], 1)

    def test_creators(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("creators in any('demo_userid',)")[0], 1)

    def test_created(self):
        """ created actually stores unix-time. Note that it's very
            likely that all objects are added within the same second.
        """
        obj = self._add_mock_meeting()
        from datetime import datetime
        from calendar import timegm
        meeting_unix = timegm(obj.created.timetuple())
        
        self.assertEqual(self.query("created == %s and path == '/meeting'" % meeting_unix)[0], 1)
        qy = ("%s < created < %s and path == '/meeting'" % (meeting_unix-1, meeting_unix+1))
        self.assertEqual(self.query(qy)[0], 1)
        

