import unittest
import os

from pyramid import testing
from pyramid.interfaces import IRequest
from zope.interface.verify import verifyObject

from voteit.core.app import register_request_factory
from voteit.core.app import init_sql_database
from voteit.core.app import register_content_types
from voteit.core.bootstrap import bootstrap_voteit


class VoteITRequestMixinTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()
        ct = """
    voteit.core.models.meeting
    voteit.core.models.site
    voteit.core.models.user
    voteit.core.models.users
        """
        self.config.registry.settings['content_types'] = ct
        register_request_factory(self.config)
        register_content_types(self.config)

        self.dbfile = '_temp_testing_sqlite.db'
        self.config.registry.settings['sqlite_file'] = 'sqlite:///%s' % self.dbfile
        init_sql_database(self.config.registry.settings)

        self.root = bootstrap_voteit(registry=self.config.registry, echo=False)

    def tearDown(self):
        os.unlink(self.dbfile)
        testing.tearDown()        

    def _make_obj(self, context=None):
        from voteit.core.testing import DummyRequestWithVoteIT
        return DummyRequestWithVoteIT(context=context)
    
    def test_verify_interface(self):
        obj = self._make_obj()
        self.assertTrue(verifyObject(IRequest, obj))

    def test_sql_session(self):
        from sqlalchemy.orm.session import Session
        obj = self._make_obj()
        self.assertTrue(isinstance(obj.sql_session, Session))
    
    def test_userid(self):
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)
        obj = self._make_obj()
        self.assertEqual(obj.userid, 'some_user')

    def test_site_root(self):
        obj = self._make_obj(context=self.root)
        self.assertEqual(obj.site_root, self.root)
    
    def test_users(self):
        from voteit.core.models.interfaces import IUsers
        obj = self._make_obj(context=self.root)
        self.assertTrue(IUsers.providedBy(obj.users))
            
    def test_user(self):
        from voteit.core.models.interfaces import IUser
        from voteit.core.models.user import User
        self.root.users['some_user'] = User()
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)
        
        obj = self._make_obj(context=self.root)
        self.assertTrue(IUser.providedBy(obj.user))

    def test_user_without_user(self):
        obj = self._make_obj(context=self.root)
        self.assertEqual(obj.user, None)
