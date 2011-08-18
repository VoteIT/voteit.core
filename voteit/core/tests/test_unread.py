import unittest
import transaction

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy

from voteit.core.bootstrap import bootstrap_voteit
from voteit.core.app import register_content_types
from voteit.core import security

from zope.interface.verify import verifyObject

from voteit.core import security
from voteit.core.testing import testing_sql_session


viewer = (security.ROLE_VIEWER, )


class UnreadTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)
        ct = """
    voteit.core.models.site
    voteit.core.models.user
    voteit.core.models.users
        """
        self.config.registry.settings['content_types'] = ct #Needed for bootstrap_voteit
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')
        self.session = testing_sql_session(self.config)
        register_content_types(self.config)
        self.root = self._fixture()

    def tearDown(self):
        testing.tearDown()
        transaction.abort() #To cancel any commit to the sql db

    def _fixture(self):
        root = bootstrap_voteit(registry=self.config.registry, echo=False)
        from voteit.core.models.user import User
        
        for userid in ('fredrik', 'anders', 'hanna', 'robin'):
            root.users[userid] = User()

        return root

    def _import_class(self):
        from voteit.core.models.unread import Unreads
        return Unreads

    def _add_mock_data(self, obj):
        data = (
            ('robin','m1', False),
            ('fredrik', 'm1', False),
            ('robin','p1', True),
            ('fredrik', 'p1', True),
            ('robin','v1', True),
            ('fredrik', 'v1', False),
         )
        for (userid, contextuid, persistent) in data:
            obj.add(userid, contextuid, persistent)

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import IUnreads
        obj = self._import_class()(self.session)
        self.assertTrue(verifyObject(IUnreads, obj))

    def test_add(self):
        obj = self._import_class()(self.session)
        userid = 'robin'
        contextuid = 'a1'
        obj.add(userid, contextuid)

        from voteit.core.models.unread import Unread
        query = self.session.query(Unread)

        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.contextuid, contextuid)

    def test_remove(self):
        obj = self._import_class()(self.session)
        self._add_mock_data(obj)
        
        userid = 'robin'
        contextuid = 'p1'
        
        obj.remove(userid, contextuid)

        from voteit.core.models.unread import Unread
        query = self.session.query(Unread).filter(Unread.userid==userid)

        self.assertEqual(len(query.all()), 2)
        
    def test_remove_userid(self):
        obj = self._import_class()(self.session)
        self._add_mock_data(obj)
        
        userid = 'robin'
        
        obj.remove_user(userid)

        from voteit.core.models.unread import Unread
        query = self.session.query(Unread).filter(Unread.userid==userid)
        
        self.assertEqual(len(query.all()), 0)

    def test_remove_context(self):
        obj = self._import_class()(self.session)
        self._add_mock_data(obj)
        
        contextuid = 'p1'
        
        obj.remove_context(contextuid)

        from voteit.core.models.unread import Unread
        query = self.session.query(Unread).filter(Unread.contextuid==contextuid)
        
        self.assertEqual(len(query.all()), 0)

    def test_retrieve(self):
        obj = self._import_class()(self.session)
        self._add_mock_data(obj)
        
        userid = 'robin'
        contextuid = 'p1'

        self.assertEqual(len(obj.retrieve(userid)), 3)
        self.assertEqual(len(obj.retrieve(userid, contextuid)), 1)

    def test_retrieve_persistentonly(self):
        obj = self._import_class()(self.session)
        self._add_mock_data(obj)

        self.assertEqual(len(obj.retrieve('robin', persistent_only=True)), 2)
        
    def test_added_subscriber_adds_to_unread(self):
        request = testing.DummyRequest()

        # Add meeting
        from voteit.core.models.meeting import Meeting
        m1 = Meeting()
        self.root['m1'] = m1
        m1.set_workflow_state(request, 'inactive')

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
        unreads = self._import_class()(self.session)
        self.assertEqual(len(unreads.retrieve('robin', 'a1')), 1)
        
    def test_content_removed_subscriber_removes_from_unread(self):
        request = testing.DummyRequest()

        # Add meeting
        from voteit.core.models.meeting import Meeting
        m1 = Meeting()
        self.root['m1'] = m1
        m1.set_workflow_state(request, 'inactive')

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
        unreads = self._import_class()(self.session)
        self.assertEqual(len(unreads.retrieve('robin', 'a1')), 0)
        
    def test_user_removed_subscriber_removes_from_unread(self):
        request = testing.DummyRequest()

        # Add meeting
        from voteit.core.models.meeting import Meeting
        m1 = Meeting()
        self.root['m1'] = m1
        m1.set_workflow_state(request, 'inactive')

        # Give users access to meeting
        m1.add_groups('robin', viewer)
        m1.add_groups('fredrik', viewer)

        #Add subscribers
        self.config.scan('voteit.core.subscribers.unread')
        
        # create agenda item
        from voteit.core.models.agenda_item import AgendaItem
        a1 = AgendaItem()
        a1.uid = 'a1'
        m1['a1'] = a1
        
        # remove user
        del self.root.users['fredrik']
        
        # check that user have no entries in unread
        unreads = self._import_class()(self.session)
        self.assertEqual(len(unreads.retrieve('fredrik')), 0)
