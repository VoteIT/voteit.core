import unittest
import tempfile

from pyramid import testing

from zope.interface.verify import verifyObject


class ExpressionsTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.dbfile = tempfile.NamedTemporaryFile() 
        from voteit.core import init_sql_database
        settings = {'sqlite_file':'sqlite:///%s' % self.dbfile}
        init_sql_database(settings)
        
        self.request = testing.DummyRequest()
        self.request.sql_session = settings['sql_session']

    def tearDown(self):
        testing.tearDown()
        self.request.sql_session.close()
        self.dbfile.close()

    def _import_class(self):
        from voteit.core.models.expression import Expressions        
        return Expressions

    def _add_mock_data(self, obj):
        data = (
            ('Like', 'robin', 'aaa'),
            ('Like', 'evis', 'aaa'),
            ('Like', 'elin', 'aaa'),
            ('Like', 'fredrik', 'aaa'),
            ('Like', 'frej', 'aaa'),
            ('Like', 'frej', 'bbb'),
            ('Like', 'frej', 'ccc'),
            ('Dislike', 'sandra', 'aaa'),
            ('Dislike', 'sandra', 'bbb'),
         )
        for (tag, userid, uid) in data:
            obj.add(tag, userid, uid)

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import IExpressions
        obj = self._import_class()(self.request)
        self.assertTrue(verifyObject(IExpressions, obj))

    def test_add(self):
        obj = self._import_class()(self.request)
        tag = 'Like'
        userid = 'robin'
        uid = 'aa-bb'
        obj.add(tag, userid, uid)

        from voteit.core.models.expression import Expression
        session = self.request.sql_session()
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

        self.assertEqual(len(obj.retrieve_userids('Like', 'aaa')), 5)
        self.assertEqual(len(obj.retrieve_userids('Like', 'bbb')), 1)
        self.assertEqual(obj.retrieve_userids('Like', 'ccc'), set(['frej']))
        self.assertEqual(len(obj.retrieve_userids('Dislike', 'aaa')), 1)
        self.assertEqual(len(obj.retrieve_userids('Dislike', 'bbb')), 1)

    def test_remove(self):
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)
        
        obj.remove('Like', 'elin', 'aaa')
        self.assertEqual(len(obj.retrieve_userids('Like', 'aaa')), 4)
