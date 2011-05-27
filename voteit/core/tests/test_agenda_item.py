import unittest

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from zope.interface.verify import verifyObject

from voteit.core import security


admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
authenticated = set([Authenticated])
participant = set([security.ROLE_PARTICIPANT])
viewer = set([security.ROLE_VIEWER])
owner = set([security.ROLE_OWNER])


class AgendaItemTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()
    
    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IAgendaItem
        obj = self._make_obj()
        self.assertTrue(verifyObject(IAgendaItem, obj))


class AgendaItemPermissionTests(unittest.TestCase):
    """ Check permissions in different agenda item states. """

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
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()
    
    def _make_meeting(self):
        from voteit.core.models.meeting import Meeting
        return Meeting()

    def test_private(self):
        obj = self._make_obj()
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator)

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)
        

    def test_active_with_closed_meeting(self):
        obj = self._make_obj()
        
        obj.set_workflow_state('inactive')
        obj.set_workflow_state('active')
        
        meeting = self._make_meeting()
        meeting.set_workflow_state('inactive')
        meeting.set_workflow_state('active')
        meeting.set_workflow_state('closed')
        
        meeting['ai'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | participant | viewer)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), set())

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())

    def test_active_with_active_meeting(self):
        obj = self._make_obj()
        
        obj.set_workflow_state('inactive')
        obj.set_workflow_state('active')
        
        meeting = self._make_meeting()
        meeting.set_workflow_state('inactive')
        meeting.set_workflow_state('active')
        
        meeting['ai'] = obj
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator | owner)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator | participant)

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)

#
    def test_closed(self):
        obj = self._make_obj()
        obj.set_workflow_state('inactive')
        obj.set_workflow_state('active')
        obj.set_workflow_state('closed')
        
        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), set())

        #Add poll
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())