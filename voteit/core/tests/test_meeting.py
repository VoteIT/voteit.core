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

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.meeting import Meeting
        return Meeting()
    
    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IMeeting
        obj = self._make_obj()
        self.assertTrue(verifyObject(IMeeting, obj))


class MeetingPermissionTests(unittest.TestCase):
    """ Check permissions in different meeting states. """

    def setUp(self):
        self.config = testing.setUp()
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        # load workflow
        from voteit.core import register_workflows
        register_workflows()

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
        obj = self._make_obj()
        obj.set_workflow_state('inactive')
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator | owner)
        
        #Meeting access
        self.assertEqual(self.pap(obj, security.REQUEST_MEETING_ACCESS), authenticated)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator | owner)

        #Manage groups
        self.assertEqual(self.pap(obj, security.MANAGE_GROUPS), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator | participant )

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)

        #Add vote
        self.assertEqual(self.pap(obj, security.ADD_VOTE), set())

    def test_active(self):
        obj = self._make_obj()
        obj.set_workflow_state('inactive')
        obj.set_workflow_state('active')
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator | owner)
        
        #Meeting access
        self.assertEqual(self.pap(obj, security.REQUEST_MEETING_ACCESS), authenticated)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator | owner)

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
        obj = self._make_obj()
        obj.set_workflow_state('inactive')
        obj.set_workflow_state('active')
        obj.set_workflow_state('closed')
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Meeting access
        self.assertEqual(self.pap(obj, security.REQUEST_MEETING_ACCESS), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

        #Manage groups
        self.assertEqual(self.pap(obj, security.MANAGE_GROUPS), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), set() )

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())

        #Add vote
        self.assertEqual(self.pap(obj, security.ADD_VOTE), set())
