import unittest

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy

from voteit.core import security
from pyramid.security import Authenticated
from zope.interface.verify import verifyObject


admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
authenticated = set([Authenticated])
participant = set([security.ROLE_PARTICIPANT])
viewer = set([security.ROLE_VIEWER])
owner = set([security.ROLE_OWNER])


class MeetingTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        # load workflow
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.meeting import Meeting
        return Meeting()
    
    def _make_ai(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IMeeting
        obj = self._make_obj()
        self.assertTrue(verifyObject(IMeeting, obj))

    def test_closing_meeting_with_active_ais(self):
        """ Closing a meeting with active agenda items should raise an exception. """
        request = testing.DummyRequest()
        ai = self._make_ai()
        ai.set_workflow_state(request, 'inactive')
        ai.set_workflow_state(request, 'active')
        obj = self._make_obj()
        obj['ai'] = ai
        
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        self.assertRaises(Exception, obj.set_workflow_state, 'closed')

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

    def _make_obj(self):
        from voteit.core.models.meeting import Meeting
        return Meeting()

    def test_private(self):
        obj = self._make_obj()
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Meeting access
        self.assertEqual(self.pap(obj, security.REQUEST_MEETING_ACCESS), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Manage groups
        self.assertEqual(self.pap(obj, security.MANAGE_GROUPS), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator)

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)
        

    def test_inactive(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'inactive')
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator | owner)
        
        #Meeting access
        self.assertEqual(self.pap(obj, security.REQUEST_MEETING_ACCESS), authenticated)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Manage groups
        self.assertEqual(self.pap(obj, security.MANAGE_GROUPS), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator | participant )

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)

        #Add vote
        self.assertEqual(self.pap(obj, security.ADD_VOTE), set())

    def test_active(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator | owner)
        
        #Meeting access
        self.assertEqual(self.pap(obj, security.REQUEST_MEETING_ACCESS), authenticated)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Manage groups
        self.assertEqual(self.pap(obj, security.MANAGE_GROUPS), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator | participant )

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)

        #Add vote
        self.assertEqual(self.pap(obj, security.ADD_VOTE), set())


#
    def test_closed(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        obj.set_workflow_state(request, 'closed')
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

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

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())

        #Add vote
        self.assertEqual(self.pap(obj, security.ADD_VOTE), set())
