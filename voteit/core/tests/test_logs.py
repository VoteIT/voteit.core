import unittest
import os

from pyramid import testing
from zope.interface.verify import verifyObject

from voteit.core import init_sql_database
from voteit.core.sql_db import make_session


class LogsTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

        self.request = testing.DummyRequest()
        settings = self.request.registry.settings

        self.dbfile = '_temp_testing_sqlite.db'
        settings['sqlite_file'] = 'sqlite:///%s' % self.dbfile
        
        init_sql_database(settings)
        
        make_session(self.request)

    def tearDown(self):
        testing.tearDown()
        #Is this really smart. Pythons tempfile module created lot's of crap that wasn't cleaned up
        os.unlink(self.dbfile)

    def _import_class(self):
        from voteit.core.models.log import Logs
        return Logs

    def _add_mock_data(self, obj):
        data = (
            ('m1', 'test', ('alert',), 'fredrik',),
            ('m1', 'test', ('log',), 'anders',),
            ('m1', 'test', ('like',), 'robin',),
            ('m1', 'test', ('alert',), 'robin',),
            ('m1', 'test', ('log',), 'hanna',),
            ('m1', 'test', ('log','alert',), 'hanna',),
         )
        for (meetinguid, message, tag, userid) in data:
            obj.add(meetinguid, message, tag, userid)

    def _init_tags(self):
        from voteit.core.models.log import Tag
        session = self.request.sql_session
        tags = ('alert', 'log', 'like',)
        for tag in tags:
            _tag = Tag(tag)
            session.add(_tag)

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import ILogs
        obj = self._import_class()(self.request)
        self.assertTrue(verifyObject(ILogs, obj))

    def test_tag(self):
        self._init_tags()
        
        from voteit.core.models.log import Tag
        session = self.request.sql_session
        query = session.query(Tag)
        self.assertEqual(len(query.all()), 3)
        self.assertEqual(len(query.filter(Tag.tag=='log').all()), 1)
        
    def test_log(self):
        meetinguid = 'm1'
        message = 'lorem ipsum'
        tags = ('log', 'alert')
        userid = 'robin'

        self._init_tags()
        session = self.request.sql_session

        from voteit.core.models.log import Tag
        _tags = []
        for tag in tags:
            _tag = session.query(Tag).filter_by(tag=tag).one()
            _tags.append(_tag)
            
            
        from voteit.core.models.log import Log
        log = Log(meetinguid, message, _tags, userid)
        session.add(log)
        
        query = session.query(Log)
        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.meetinguid, meetinguid)
        self.assertEqual(result_obj.message, message)
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(len(result_obj.tags), 2)
        
    
    def test_add(self):
        self._init_tags()
        
        obj = self._import_class()(self.request)
        meetinguid = 'a1'
        message = 'aa-bb'
        tag = ('log', 'alert')
        userid = 'robin'
        obj.add(meetinguid, message, tag, userid)

        from voteit.core.models.log import Log
        session = self.request.sql_session
        query = session.query(Log)

        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.meetinguid, meetinguid)
        self.assertEqual(result_obj.message, message)
        self.assertEqual(len(result_obj.tags), 2)

    def test_retrieve_entries(self):
        self._init_tags()
        
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)

        #FIXME: this will fail because of missing fetures
        self.assertEqual(len(obj.retrieve_entries('m1', tag='log')), 3)


