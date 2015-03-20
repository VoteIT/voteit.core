import unittest
 
from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
 
from voteit.core import security
from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.models.interfaces import IUnread
 
 
class UnreadTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
        self.config.include('arche.testing')
        self.config.include('arche.testing.setup_auth')
        self.config.include('voteit.core.models.meeting')

    def tearDown(self):
        testing.tearDown()
 
    def _fixture_and_setup(self):
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.user import User
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        for userid in ('fredrik', 'anders', 'hanna', 'robin'):
            root.users[userid] = User()
        root['m'] = Meeting()
        root['m']['ai'] = ai = AgendaItem()
        security.unrestricted_wf_transition_to(ai, 'upcoming')
        ai['p'] = Proposal()
        return ai['p']

    @property
    def _cut(self):
        from voteit.core.models.unread import Unread
        return Unread
 
    def test_verify_class(self):
        self.assertTrue(verifyClass(IUnread, self._cut))
 
    def test_verify_obj(self):
        context = self._fixture_and_setup()
        obj = self._cut(context)
        self.assertTrue(verifyObject(IUnread, obj))
 
    def test_mark_as_read(self):
        context = self._fixture_and_setup()
        obj = self._cut(context)
        userid = 'somebody'
        obj.unread_storage.add(userid)
        self.assertTrue(userid in obj.get_unread_userids())
        obj.mark_as_read(userid)
        self.assertFalse(userid in obj.get_unread_userids())
 
    def test_unread_on_check(self):
        context = self._fixture_and_setup()
        obj = self._cut(context)
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin',)))
 
    def test_only_viewers_added(self):
        context = self._fixture_and_setup()
        meeting = context.__parent__.__parent__
        meeting.add_groups('hanna', [security.ROLE_VIEWER])
        meeting.add_groups('anders', [security.ROLE_VIEWER])
        obj = self._cut(context)
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin', 'hanna', 'anders')))
 
    def test_reset_unread(self):
        context = self._fixture_and_setup()
        meeting = context.__parent__.__parent__
        meeting.add_groups('hanna', [security.ROLE_VIEWER])
        meeting.add_groups('anders', [security.ROLE_VIEWER])
        obj = self._cut(context)
        obj.mark_as_read('hanna')
        obj.reset_unread()
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin', 'hanna', 'anders')))

    def test_integration(self):
        context = self._fixture_and_setup()
        self.config.include('voteit.core.models.unread')
        self.failUnless(IUnread(context, None))
