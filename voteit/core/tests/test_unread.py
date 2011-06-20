import unittest
import os

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from zope.interface.verify import verifyObject

from voteit.core import init_sql_database
from voteit.core.sql_db import make_session
from voteit.core import security


viewer = set([security.ROLE_VIEWER])


class UnreadTests(unittest.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

        settings = {}
        self.dbfile = '_temp_testing_sqlite.db'
        settings['sqlite_file'] = 'sqlite:///%s' % self.dbfile
        init_sql_database(settings)
        self.request.registry.settings = settings
        make_session(self.request)
        
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()
        #Is this really smart. Pythons tempfile module created lot's of crap that wasn't cleaned up
        os.unlink(self.dbfile)

    def _import_class(self):
        from voteit.core.models.unread import Unreads
        return Unreads

    def _add_mock_data(self, obj):
        data = (
            ('robin','m1', ),
            ('fredrik', 'm1'),
            ('robin','p1'),
            ('fredrik', 'p1'),
            ('robin','v1'),
            ('fredrik', 'v1'),
         )
        for (userid, contextuid) in data:
            obj.add(userid, contextuid)

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import IUnreads
        obj = self._import_class()(self.request)
        self.assertTrue(verifyObject(IUnreads, obj))

    def test_add(self):
        obj = self._import_class()(self.request)
        userid = 'robin'
        contextuid = 'a1'
        obj.add(userid, contextuid)

        from voteit.core.models.unread import Unread
        session = self.request.sql_session
        query = session.query(Unread)

        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.contextuid, contextuid)

    def test_remove(self):
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)
        
        userid = 'robin'
        contextuid = 'p1'
        
        obj.remove(userid, contextuid)

        from voteit.core.models.unread import Unread
        session = self.request.sql_session
        query = session.query(Unread).filter(Unread.userid==userid)

        self.assertEqual(len(query.all()), 2)
        
    def test_remove_userid(self):
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)
        
        userid = 'robin'
        
        obj.remove_user(userid)

        from voteit.core.models.unread import Unread
        session = self.request.sql_session
        query = session.query(Unread).filter(Unread.userid==userid)
        
        self.assertEqual(len(query.all()), 0)

    def test_remove_context(self):
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)
        
        contextuid = 'p1'
        
        obj.remove_context(contextuid)

        from voteit.core.models.unread import Unread
        session = self.request.sql_session
        query = session.query(Unread).filter(Unread.contextuid==contextuid)
        
        self.assertEqual(len(query.all()), 0)

    def test_retrieve(self):
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)
        
        userid = 'robin'
        contextuid = 'p1'

        self.assertEqual(len(obj.retrieve(userid)), 3)
        self.assertEqual(len(obj.retrieve(userid, contextuid)), 1)
        
    def test_added_subscriber_adds_to_unread(self):
        policy = ACLAuthorizationPolicy()
        pap = policy.principals_allowed_by_permission
    
        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.users import Users
        root['users'] = Users()
        
        # Add users to site
        from voteit.core.models.user import User
        u1 = User()
        root.users['robin'] = u1
        u2 = User()
        root.users['fredrik'] = u2

        # Add meeting
        from voteit.core.models.meeting import Meeting
        m1 = Meeting()
        root['m1'] = m1

        # Give users access to meeting
        m1.set_groups('robin', viewer)
        m1.set_groups('fredrik', viewer)

        #Add subscribers
        self.config.scan('voteit.core.subscribers.unread')
        
        # create agenda item
        from voteit.core.models.agenda_item import AgendaItem
        a1 = AgendaItem()
        a1.uid = 'a1'
        m1['a1'] = a1

        # check that users have entries in unread
        unreads = self._import_class()(self.request)
        self.assertEqual(len(unreads.retrieve('robin', 'a1')), 1)
        
    def test_content_removed_subscriber_removes_from_unread(self):
        policy = ACLAuthorizationPolicy()
        pap = policy.principals_allowed_by_permission
    
        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.users import Users
        root['users'] = Users()
        
        # Add users to site
        from voteit.core.models.user import User
        u1 = User()
        root.users['robin'] = u1
        u2 = User()
        root.users['fredrik'] = u2

        # Add meeting
        from voteit.core.models.meeting import Meeting
        m1 = Meeting()
        root['m1'] = m1

        # Give users access to meeting
        m1.set_groups('robin', viewer)
        m1.set_groups('fredrik', viewer)

        #Add subscribers
        self.config.scan('voteit.core.subscribers.unread')
        
        # create agenda item
        from voteit.core.models.agenda_item import AgendaItem
        a1 = AgendaItem()
        a1.uid = 'a1'
        m1['a1'] = a1
        
        # remove agenda item
        del m1['a1']
        
        # check that user have no entries in unread for agenda item
        unreads = self._import_class()(self.request)
        self.assertEqual(len(unreads.retrieve('robin', 'a1')), 0)
        
    def test_user_removed_subscriber_removes_from_unread(self):
        policy = ACLAuthorizationPolicy()
        pap = policy.principals_allowed_by_permission
    
        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.users import Users
        root['users'] = Users()
        
        # Add users to site
        from voteit.core.models.user import User
        u1 = User()
        root.users['robin'] = u1
        u2 = User()
        root.users['fredrik'] = u2

        # Add meeting
        from voteit.core.models.meeting import Meeting
        m1 = Meeting()
        root['m1'] = m1

        # Give users access to meeting
        m1.set_groups('robin', viewer)
        m1.set_groups('fredrik', viewer)

        #Add subscribers
        self.config.scan('voteit.core.subscribers.unread')
        
        # create agenda item
        from voteit.core.models.agenda_item import AgendaItem
        a1 = AgendaItem()
        a1.uid = 'a1'
        m1['a1'] = a1
        
        # remove user
        del root.users['fredrik']
        
        # check that user have no entries in unread
        unreads = self._import_class()(self.request)
        self.assertEqual(len(unreads.retrieve('fredrik')), 0)
