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
from voteit.core.testing_helpers import bootstrap_and_fixture


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
        self.config.include('arche.utils')
        self.config.include('arche.security')
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
        self.config.include('voteit.core.subscribers.timestamps') #To add subscriber
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

    def test_get_ticket_names(self):
        self.config.include('arche.testing')
        self.config.include('voteit.core.models.invite_ticket')
        obj = self._cut()
        obj.add_invite_ticket('john@doe.com', [security.ROLE_DISCUSS])
        obj.add_invite_ticket('jane@doe.com', [security.ROLE_MODERATOR])
        results = obj.get_ticket_names(previous_invites = 0)
        self.assertEqual(set(results), set(['john@doe.com', 'jane@doe.com']))

    def test_add_invite_ticket_doesnt_touch_existing(self):
        self.config.include('arche')
        self.config.include('voteit.core.models.invite_ticket')
        obj = self._cut()
        self.failUnless(obj.add_invite_ticket('john@doe.com', [security.ROLE_DISCUSS]))
        self.failIf(obj.add_invite_ticket('john@doe.com', [security.ROLE_DISCUSS]))

    def test_add_default_portlets_meeting(self):
        from voteit.core.models.meeting import add_default_portlets_meeting
        from arche.interfaces import IPortletManager
        self.config.include('arche')
        self.config.include('voteit.core.portlets')
        obj = self._cut()
        add_default_portlets_meeting(obj)
        manager = IPortletManager(obj)
        portlet_types = [x.portlet_type for x in manager['agenda_item'].values()]
        self.assertIn('ai_polls', portlet_types)
        self.assertIn('ai_proposals', portlet_types)
        self.assertIn('ai_discussions', portlet_types)

    def test_add_default_portlets_duplicate_no_harm(self):
        from voteit.core.models.meeting import add_default_portlets_meeting
        from arche.interfaces import IPortletManager
        self.config.include('arche')
        self.config.include('voteit.core.portlets')
        obj = self._cut()
        add_default_portlets_meeting(obj)
        manager = IPortletManager(obj)
        first_count = len(manager['agenda_item'])
        add_default_portlets_meeting(obj)
        second_count = len(manager['agenda_item'])
        self.assertEqual(first_count, second_count)


class MeetingPermissionTests(unittest.TestCase):
    """ Check permissions in different meeting states. """

    def setUp(self):
        self.config = testing.setUp()
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        # load workflow
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')
        self.config.include('arche.security')
        self.config.include('arche.utils')
        self.config.include('voteit.core.models.meeting')

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
        self.assertEqual(self.pap(obj, security.MANAGE_GROUPS), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), set() )

        #Add discussion post
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), set() )

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())

        #Add vote
        self.assertEqual(self.pap(obj, security.ADD_VOTE), set())
