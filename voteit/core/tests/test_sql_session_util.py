import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from sqlalchemy import create_engine


class SQLSessionUtilTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _class(self):
        from voteit.core.models.sql_session import SQLSession        
        return SQLSession

    def _make_obj(self):
        klass = self._class()
        engine = create_engine('sqlite://')
        return klass(engine)
        
    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import ISQLSession
        self.assertTrue(verifyObject(ISQLSession, self._make_obj()))

    def test_app_add_sql_session_util(self):
        from voteit.core.app import add_sql_session_util
        add_sql_session_util(self.config, sqlite_file='sqlite://')
        from voteit.core.models.interfaces import ISQLSession
        util = self.config.registry.queryUtility(ISQLSession)
        self.assertTrue(ISQLSession.providedBy(util))

    def test_scoped_sessions(self):
        obj = self._make_obj()
        session1 = obj()
        session2 = obj()
        self.assertEqual(session1, session2)
        