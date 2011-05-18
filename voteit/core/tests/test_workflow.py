import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.configuration import xmlconfig
from repoze.workflow import get_workflow
from pyramid.threadlocal import get_current_request

from voteit.core.models.site import SiteRoot
from voteit.core.models.meeting import Meeting
from voteit.core.models.agenda_item import AgendaItem
from voteit.core.models.proposal import Proposal
from voteit.core.models.poll import Poll

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _load_workflows(self):
        # load workflow
        from voteit.core import register_workflows
        register_workflows()
        
    def test_verify_workflow(self):
        self._load_workflows()
        
        workflow = get_workflow(SiteRoot, SiteRoot.__name__)
        self.assertEqual(workflow, None)
        
        workflow = get_workflow(Meeting, Meeting.__name__)
        self.assertEqual(workflow.name, u'Meeting Workflow')
        
        workflow = get_workflow(AgendaItem, AgendaItem.__name__)
        self.assertEqual(workflow.name, u'Agenda Item Workflow')
        
        workflow = get_workflow(Proposal, Proposal.__name__)
        self.assertEqual(workflow.name, u'Proposal Workflow')
        
        workflow = get_workflow(Poll, Poll.__name__)
        self.assertEqual(workflow.name, u'Poll Workflow')
        
    def test_meeting_states(self):
        self._load_workflows()
        
        obj = Meeting()

        self.assertEqual(obj.get_workflow_state, u'private')

        obj.make_workflow_transition('private_to_inactive')
        self.assertEqual(obj.get_workflow_state, u'inactive')

        obj.make_workflow_transition('inactive_to_active')
        self.assertEqual(obj.get_workflow_state, u'active')

        obj.reset_workflow()
        obj.make_workflow_transition('private_to_inactive')
        obj.make_workflow_transition('inactive_to_closed')
        self.assertEqual(obj.get_workflow_state, u'closed')

        obj.reset_workflow()
        obj.make_workflow_transition('private_to_inactive')
        obj.make_workflow_transition('inactive_to_active')
        obj.make_workflow_transition('active_to_inactive')
        self.assertEqual(obj.get_workflow_state, u'inactive')

        obj.reset_workflow()
        obj.make_workflow_transition('private_to_inactive')
        obj.make_workflow_transition('inactive_to_active')
        obj.make_workflow_transition('active_to_closed')
        self.assertEqual(obj.get_workflow_state, u'closed')
        
        obj.reset_workflow()
        obj.make_workflow_transition('private_to_inactive')
        obj.make_workflow_transition('inactive_to_closed')
        obj.make_workflow_transition('closed_to_active')
        self.assertEqual(obj.get_workflow_state, u'active')
        
        obj.reset_workflow()
        obj.make_workflow_transition('private_to_inactive')
        obj.make_workflow_transition('inactive_to_closed')
        obj.make_workflow_transition('closed_to_inactive')
        self.assertEqual(obj.get_workflow_state, u'inactive')
        
    def test_agenda_item_states(self):
        self._load_workflows()
        
        obj = AgendaItem()
        
        workflow = get_workflow(AgendaItem, AgendaItem.__name__, obj)
        obj.reset_workflow()
        self.assertEqual(obj.get_workflow_state, u'private')

        obj.make_workflow_transition('private_to_inactive')
        self.assertEqual(obj.get_workflow_state, u'inactive')

        obj.make_workflow_transition('inactive_to_active')
        self.assertEqual(obj.get_workflow_state, u'active')

        obj.reset_workflow()
        obj.make_workflow_transition('private_to_inactive')
        obj.make_workflow_transition('inactive_to_closed')
        self.assertEqual(obj.get_workflow_state, u'closed')

        obj.reset_workflow()
        obj.make_workflow_transition('private_to_inactive')
        obj.make_workflow_transition('inactive_to_active')
        obj.make_workflow_transition('active_to_inactive')
        self.assertEqual(obj.get_workflow_state, u'inactive')

        obj.reset_workflow()
        obj.make_workflow_transition('private_to_inactive')
        obj.make_workflow_transition('inactive_to_active')
        obj.make_workflow_transition('active_to_closed')
        self.assertEqual(obj.get_workflow_state, u'closed')
        
        obj.reset_workflow()
        obj.make_workflow_transition('private_to_inactive')
        obj.make_workflow_transition('inactive_to_closed')
        obj.make_workflow_transition('closed_to_active')
        self.assertEqual(obj.get_workflow_state, u'active')
        
        obj.reset_workflow()
        obj.make_workflow_transition('private_to_inactive')
        obj.make_workflow_transition('inactive_to_closed')
        obj.make_workflow_transition('closed_to_inactive')
        self.assertEqual(obj.get_workflow_state, u'inactive')
        
    def test_proposal_states(self):
        self._load_workflows()
        
        obj = Proposal()
        
        workflow = get_workflow(Proposal, Proposal.__name__, obj)
        obj.reset_workflow()
        self.assertEqual(obj.get_workflow_state, u'published')

        obj.make_workflow_transition('published_to_retracted')
        self.assertEqual(obj.get_workflow_state, u'retracted')

        obj.reset_workflow()
        obj.make_workflow_transition('published_to_voting')
        self.assertEqual(obj.get_workflow_state, u'voting')

        obj.make_workflow_transition('voting_to_approved')
        self.assertEqual(obj.get_workflow_state, u'approved')
        
        obj.make_workflow_transition('approved_to_finished')
        self.assertEqual(obj.get_workflow_state, u'finished')

        obj.reset_workflow()
        obj.make_workflow_transition('published_to_voting')
        obj.make_workflow_transition('voting_to_denied')
        self.assertEqual(obj.get_workflow_state, u'denied')
        
        obj.make_workflow_transition('denied_to_finished')
        self.assertEqual(obj.get_workflow_state, u'finished')
        
    def test_poll_states(self):
        self._load_workflows()
        
        obj = Poll()
        
        workflow = get_workflow(Poll, Poll.__name__, obj)
        obj.reset_workflow()
        self.assertEqual(obj.get_workflow_state, u'private')

        obj.make_workflow_transition('private_to_ongoing')
        self.assertEqual(obj.get_workflow_state, u'ongoing')

        obj.make_workflow_transition('ongoing_to_closed')
        self.assertEqual(obj.get_workflow_state, u'closed')
        
        obj.reset_workflow()
        obj.make_workflow_transition('private_to_ongoing')
        obj.make_workflow_transition('ongoing_to_cancelled')
        self.assertEqual(obj.get_workflow_state, u'cancelled')

        obj.reset_workflow()
        obj.make_workflow_transition('private_to_ongoing')
        obj.make_workflow_transition('ongoing_to_private')
        self.assertEqual(obj.get_workflow_state, u'private')
        
    def test_meeting_transitions(self):
        self._load_workflows()
        
        obj = Meeting()

        states = obj.get_workflow_states()
