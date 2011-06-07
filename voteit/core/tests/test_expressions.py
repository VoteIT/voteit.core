import unittest
import os

from pyramid import testing
from zope.interface.verify import verifyObject

from voteit.core import init_sql_database
from voteit.core.sql_db import make_session


class ExpressionsTests(unittest.TestCase):
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
        from voteit.core.models.expression import Expressions        
        return Expressions

    def _add_mock_data(self, obj):
        data = (
            (u'Like', u'robin', u'aaa'),
            (u'Like', u'evis', u'aaa'),
            (u'Like', u'elin', u'aaa'),
            (u'Like', u'fredrik', u'aaa'),
            (u'Like', u'frej', u'aaa'),
            (u'Like', u'frej', u'bbb'),
            (u'Like', u'frej', u'ccc'),
            (u'Dislike', u'sandra', u'aaa'),
            (u'Dislike', u'sandra', u'bbb'),
         )
        for (tag, userid, uid) in data:
            obj.add(tag, userid, uid)

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import IExpressions
        obj = self._import_class()(self.request)
        self.assertTrue(verifyObject(IExpressions, obj))

    def test_add(self):
        obj = self._import_class()(self.request)
        tag = u'Like'
        userid = u'robin'
        uid = u'aa-bb'
        obj.add(tag, userid, uid)

        from voteit.core.models.expression import Expression
        session = self.request.sql_session
        query = session.query(Expression).filter_by(tag=tag, userid=userid, uid=uid)

        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.uid, uid)
        self.assertEqual(result_obj.tag, tag)
        self.assertEqual(result_obj.userid, userid)

    def test_retrieve_userids(self):
        """ Must be unique in uid and tag. """
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)

        self.assertEqual(len(obj.retrieve_userids(u'Like', u'aaa')), 5)
        self.assertEqual(len(obj.retrieve_userids(u'Like', u'bbb')), 1)
        self.assertEqual(obj.retrieve_userids(u'Like', u'ccc'), set([u'frej']))
        self.assertEqual(len(obj.retrieve_userids(u'Dislike', u'aaa')), 1)
        self.assertEqual(len(obj.retrieve_userids(u'Dislike', u'bbb')), 1)

    def test_remove(self):
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)
        
        obj.remove(u'Like', u'elin', u'aaa')
        self.assertEqual(len(obj.retrieve_userids(u'Like', u'aaa')), 4)
