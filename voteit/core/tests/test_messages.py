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
            ('robin', 'aaa'),
            ('evis', 'aaa'),
            ('elin', 'aaa'),
            ('fredrik', 'aaa'),
            ('frej', 'aaa'),
            ('frej', 'bbb'),
            ('frej', 'ccc'),
            ('sandra', 'aaa'),
            ('sandra', 'bbb'),
         )
        for (userid, message) in data:
            obj.add(userid, message)

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import IMessages
        obj = self._import_class()(self.request)
        self.assertTrue(verifyObject(IMessages, obj))

    def test_add(self):
        obj = self._import_class()(self.request)
        userid = 'robin'
        message = 'aa-bb'
        obj.add(userid, message)

        from voteit.core.models.message import Message
        session = self.request.sql_session
        query = session.query(Message).filter_by(userid=userid)

        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.message, message)

    def test_retrieve_user_messages(self):
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)

        self.assertEqual(len(obj.retrieve_user_messages('frej')), 3)

    def test_remove(self):
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)
        
        messages = obj.retrieve_user_messages('frej')
        obj.remove('frej', messages[0].id)
        self.assertEqual(len(obj.retrieve_user_messages('frej')), 2)
