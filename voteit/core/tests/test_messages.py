import unittest
import os

from pyramid import testing
from zope.interface.verify import verifyObject

from voteit.core import init_sql_database
from voteit.core.sql_db import make_session


class MessagesTests(unittest.TestCase):
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
        from voteit.core.models.message import Messages
        return Messages

    def _add_mock_data(self, obj):
        data = (
            ('m1', 'test', 'alert', None, None,),
            ('m1', 'test', 'log', 'm1', None,),
            ('m1', 'test', 'like', 'p1', 'robin',),
            ('m1', 'test', 'alert', 'v1', 'robin',),
            ('m1', 'test', 'log', 'p1', None,),
            ('m1', 'test', 'log', 'v1', None,),
         )
        for (meetinguid, message, tag, contextuid, userid) in data:
            obj.add(meetinguid, message, tag, contextuid, userid)

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import IMessages
        obj = self._import_class()(self.request)
        self.assertTrue(verifyObject(IMessages, obj))

    def test_add(self):
        obj = self._import_class()(self.request)
        meetinguid = 'a1'
        message = 'aa-bb'
        tag = 'log'
        contextuid = 'a1'
        userid = 'robin'
        obj.add(meetinguid, message, tag, contextuid, userid)

        from voteit.core.models.message import Message
        session = self.request.sql_session
        query = session.query(Message).filter_by(userid=userid)

        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.meetinguid, meetinguid)
        self.assertEqual(result_obj.message, message)
        self.assertEqual(result_obj.tag, tag)

    def test_retrieve_user_messages(self):
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)

        self.assertEqual(len(obj.retrieve_messages('m1', contextuid='v1')), 2)
