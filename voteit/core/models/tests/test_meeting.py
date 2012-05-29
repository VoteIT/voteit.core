import unittest
from datetime import datetime

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from pyramid.httpexceptions import HTTPForbidden
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core import security
from voteit.core.models.interfaces import IMeeting
from voteit.core.testing_helpers import register_workflows

admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
authenticated = set([Authenticated])
discuss = set([security.ROLE_DISCUSS])
propose = set([security.ROLE_PROPOSE])
viewer = set([security.ROLE_VIEWER])
voter = set([security.ROLE_VOTER])
owner = set([security.ROLE_OWNER])


class MeetingTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.meeting import Meeting
        return Meeting

    @property
    def _ai(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem

    def test_verify_class(self):
        self.assertTrue(verifyClass(IMeeting, self._cut))

    def test_verify_obj(self):
        self.assertTrue(verifyObject(IMeeting, self._cut()))

    def test_meeting_with_one_creator_sets_creator_as_moderator(self):
        obj = self._cut(creators = ['jane'])
        self.assertIn('role:Moderator', obj.get_groups('jane'))

    def test_closing_meeting_with_ongoing_ais(self):
        """ Closing a meeting with ongoing agenda items should raise an exception. """
        register_workflows(self.config)
        request = testing.DummyRequest()
        ai = self._ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        obj = self._cut()
        obj['ai'] = ai
        
        obj.set_workflow_state(request, 'ongoing')
        self.assertRaises(Exception, obj.set_workflow_state, 'closed')

    def test_timestamp_added_on_close(self):
        register_workflows(self.config)
        self.config.scan('voteit.core.subscribers.timestamps') #To add subscriber
        request = testing.DummyRequest()
        obj = self._cut()
        obj.set_workflow_state(request, 'ongoing')
        self.assertFalse(isinstance(obj.end_time, datetime))
        obj.set_workflow_state(request, 'closed')
        self.assertTrue(isinstance(obj.end_time, datetime))

    def test_closing_meeting_callback(self):
        register_workflows(self.config)
        request = testing.DummyRequest()
        obj = self._cut()
        obj['ai'] = self._ai()
        obj.set_workflow_state(request, 'ongoing')
        obj['ai'].set_workflow_state(request, 'upcoming')
        obj['ai'].set_workflow_state(request, 'ongoing')
        self.assertRaises(HTTPForbidden, obj.set_workflow_state, request, 'closed')

    def test_add_invite_ticket_traversal(self):
        from voteit.core.models.invite_ticket import InviteTicket
        self.config.include('pyramid_mailer.testing')
        self.config.scan('voteit.core.views.components.email')
        request = testing.DummyRequest()
        obj = self._cut()
        ticket = InviteTicket('blabla@hello.se', ['role:Moderator'], 'Hello!')
        obj.add_invite_ticket(ticket, request)
        self.assertEqual(obj, ticket.__parent__)


class MeetingPermissionTests(unittest.TestCase):
    """ Check permissions in different meeting states. """

    def setUp(self):
        self.config = testing.setUp()
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        # load workflow
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.meeting import Meeting
        return Meeting

    def test_upcoming(self):
        request = testing.DummyRequest()
        obj = self._cut()
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator )
        
        #Meeting access
        self.assertEqual(self.pap(obj, security.REQUEST_MEETING_ACCESS), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Manage groups
        self.assertEqual(self.pap(obj, security.MANAGE_GROUPS), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator | propose )

        #Add discussion post
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), admin | moderator | discuss )

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)

        #Add vote
        self.assertEqual(self.pap(obj, security.ADD_VOTE), set())

    def test_ongoing(self):
        request = testing.DummyRequest()
        obj = self._cut()
        obj.set_workflow_state(request, 'ongoing')
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator )
        
        #Meeting access
        self.assertEqual(self.pap(obj, security.REQUEST_MEETING_ACCESS), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Manage groups
        self.assertEqual(self.pap(obj, security.MANAGE_GROUPS), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator | propose )

        #Add discussion post
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), admin | moderator | discuss )

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)

        #Add vote
        self.assertEqual(self.pap(obj, security.ADD_VOTE), set())

    def test_closed(self):
        request = testing.DummyRequest()
        obj = self._cut()
        obj.set_workflow_state(request, 'ongoing')
        obj.set_workflow_state(request, 'closed')
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Meeting access
        self.assertEqual(self.pap(obj, security.REQUEST_MEETING_ACCESS), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin)

        #Manage groups
        self.assertEqual(self.pap(obj, security.MANAGE_GROUPS), admin )

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), set() )

        #Add discussion post
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), set() )

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())

        #Add vote
        self.assertEqual(self.pap(obj, security.ADD_VOTE), set())
