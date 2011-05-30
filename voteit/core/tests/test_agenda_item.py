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
        from voteit.core import register_workflows
        register_workflows()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()

    def _make_proposal(self):
        from voteit.core.models.proposal import Proposal
        return Proposal()
    
    def _make_poll(self):
        from voteit.core.models.poll import Poll
        return Poll()

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IAgendaItem
        obj = self._make_obj()
        self.assertTrue(verifyObject(IAgendaItem, obj))

    def test_workflow_closed_state_marks_proposals_unhandled(self):
        """ Published proposals should be marked as 'unhandled' when
            an AI closes.
        """
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj['proposal'] = self._make_proposal() #Should be published as initial state
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        obj.set_workflow_state(request ,'closed')
        self.assertEqual(obj['proposal'].get_workflow_state(), u'unhandled')


    def test_workflow_closed_state_active_poll_exception(self):
        """ When you try to close an agenda items that has an ongoing
            poll in it, it should raise an exception.
        """
        request = testing.DummyRequest()
        obj = self._make_obj()

        obj['poll'] = self._make_poll()
        obj['poll'].set_workflow_state(request, 'planned')
        obj['poll'].set_workflow_state(request, 'ongoing')

        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        self.assertRaises(Exception, obj.set_workflow_state, 'closed')
        

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
        request = testing.DummyRequest()
        obj = self._make_obj()
        
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'inactive')
        meeting.set_workflow_state(request, 'active')
        meeting.set_workflow_state(request, 'closed')
        
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
        request = testing.DummyRequest()
        obj = self._make_obj()
        
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'inactive')
        meeting.set_workflow_state(request, 'active')
        
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
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'inactive')
        obj.set_workflow_state(request, 'active')
        obj.set_workflow_state(request, 'closed')
        
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
