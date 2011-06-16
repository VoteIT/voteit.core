import unittest
import os

from pyramid import testing
from zope.interface.verify import verifyObject

from voteit.core import init_sql_database
from voteit.core.sql_db import make_session

class EventTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

        self.request = testing.DummyRequest()
        settings = self.request.registry.settings

        self.dbfile = '_temp_testing_sqlite.db'
        settings['sqlite_file'] = 'sqlite:///%s' % self.dbfile
        
        init_sql_database(settings)
        
        make_session(self.request)
        
        self.config.scan('voteit.core.event_handlers')

    def tearDown(self):
        testing.tearDown()
        #Is this really smart. Pythons tempfile module created lot's of crap that wasn't cleaned up
        os.unlink(self.dbfile)
        
    def _make_root(self):
        from voteit.core.models.site import SiteRoot
        return SiteRoot()
        
    def _make_logs(self):
        from voteit.core.models.log import Logs
        return Logs(self.request)

    def test_meeting_added(self):
        root = self._make_root()
    
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting
        
        #FIXME: Until we can use a utility or similar to fetch a currently active SQL session,
        #this code will be broken. :(
        logs = self._make_logs()
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='added', primaryuid=meeting.uid)), 1)
