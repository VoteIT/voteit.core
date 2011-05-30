import unittest

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy

from voteit.core import security
from pyramid.security import Authenticated
from zope.interface.verify import verifyObject


admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
participant = set([security.ROLE_PARTICIPANT])
viewer = set([security.ROLE_VIEWER])
owner = set([security.ROLE_OWNER])


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.proposal import Proposal
        return Proposal()
    
    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IProposal
        obj = self._make_obj()
        self.assertTrue(verifyObject(IProposal, obj))


class ProposalPermissionTests(unittest.TestCase):
    """ Check permissions in different meeting and agenda item states.
        Note that the add permission is handled by the agenda item / meeting.
    """

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
        from voteit.core.models.proposal import Proposal
        return Proposal()
    
    def _make_ai(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()

    def test_published(self):
        obj = self._make_obj()

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), admin | moderator | owner)

    def test_retracted_in_active_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'retracted')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'inactive')
        ai.set_workflow_state(request, 'active')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_retracted_in_closed_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'retracted')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'inactive')
        ai.set_workflow_state(request, 'active')
        ai.set_workflow_state(request, 'closed')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_unhandled_in_closed_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'unhandled')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'inactive')
        ai.set_workflow_state(request, 'active')
        ai.set_workflow_state(request, 'closed')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_approved_in_active_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'voting')
        obj.set_workflow_state(request, 'approved')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'inactive')
        ai.set_workflow_state(request, 'active')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())

    def test_approved_in_closed_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'voting')
        obj.set_workflow_state(request, 'approved')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'inactive')
        ai.set_workflow_state(request, 'active')
        ai.set_workflow_state(request, 'closed')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())

    def test_denied_in_active_ai(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'voting')
        obj.set_workflow_state(request, 'denied')
        ai = self._make_ai()
        ai.set_workflow_state(request, 'inactive')
        ai.set_workflow_state(request, 'active')
        ai['prop'] = obj

        #View
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer | participant | owner)

        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)

        #Retract
        self.assertEqual(self.pap(obj, security.RETRACT), set())
