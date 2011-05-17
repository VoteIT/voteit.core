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
        # FIXME: use package-relative dotted name insted of absolute path
        xmlconfig.file('voteit/core/workflows/meeting.xml', execute=True)
        xmlconfig.file('voteit/core/workflows/agenda_item.xml', execute=True)
        xmlconfig.file('voteit/core/workflows/proposal.xml', execute=True)
        xmlconfig.file('voteit/core/workflows/poll.xml', execute=True)
        
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
        xmlconfig.file('voteit/core/workflows/meeting.xml', execute=True)
        request = get_current_request()
        
        obj = Meeting()
        
        workflow = get_workflow(Meeting, Meeting.__name__, obj)
        workflow.initialize(obj)
        self.assertEqual(workflow.state_of(obj), u'private')

        workflow.transition(obj, request, 'private_to_inactive')
        self.assertEqual(workflow.state_of(obj), u'inactive')

        workflow.transition(obj, request, 'inactive_to_active')
        self.assertEqual(workflow.state_of(obj), u'active')

        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_inactive')
        workflow.transition(obj, request, 'inactive_to_closed')
        self.assertEqual(workflow.state_of(obj), u'closed')

        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_inactive')
        workflow.transition(obj, request, 'inactive_to_active')
        workflow.transition(obj, request, 'active_to_inactive')
        self.assertEqual(workflow.state_of(obj), u'inactive')

        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_inactive')
        workflow.transition(obj, request, 'inactive_to_active')
        workflow.transition(obj, request, 'active_to_closed')
        self.assertEqual(workflow.state_of(obj), u'closed')
        
        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_inactive')
        workflow.transition(obj, request, 'inactive_to_closed')
        workflow.transition(obj, request, 'closed_to_active')
        self.assertEqual(workflow.state_of(obj), u'active')
        
        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_inactive')
        workflow.transition(obj, request, 'inactive_to_closed')
        workflow.transition(obj, request, 'closed_to_inactive')
        self.assertEqual(workflow.state_of(obj), u'inactive')
        
    def test_agenda_item_states(self):
        xmlconfig.file('voteit/core/workflows/agenda_item.xml', execute=True)
        request = get_current_request()
        
        obj = AgendaItem()
        
        workflow = get_workflow(AgendaItem, AgendaItem.__name__, obj)
        workflow.initialize(obj)
        self.assertEqual(workflow.state_of(obj), u'private')

        workflow.transition(obj, request, 'private_to_inactive')
        self.assertEqual(workflow.state_of(obj), u'inactive')

        workflow.transition(obj, request, 'inactive_to_active')
        self.assertEqual(workflow.state_of(obj), u'active')

        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_inactive')
        workflow.transition(obj, request, 'inactive_to_closed')
        self.assertEqual(workflow.state_of(obj), u'closed')

        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_inactive')
        workflow.transition(obj, request, 'inactive_to_active')
        workflow.transition(obj, request, 'active_to_inactive')
        self.assertEqual(workflow.state_of(obj), u'inactive')

        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_inactive')
        workflow.transition(obj, request, 'inactive_to_active')
        workflow.transition(obj, request, 'active_to_closed')
        self.assertEqual(workflow.state_of(obj), u'closed')
        
        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_inactive')
        workflow.transition(obj, request, 'inactive_to_closed')
        workflow.transition(obj, request, 'closed_to_active')
        self.assertEqual(workflow.state_of(obj), u'active')
        
        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_inactive')
        workflow.transition(obj, request, 'inactive_to_closed')
        workflow.transition(obj, request, 'closed_to_inactive')
        self.assertEqual(workflow.state_of(obj), u'inactive')
        
    def test_proposal_states(self):
        xmlconfig.file('voteit/core/workflows/proposal.xml', execute=True)
        request = get_current_request()
        
        obj = Proposal()
        
        workflow = get_workflow(Proposal, Proposal.__name__, obj)
        workflow.initialize(obj)
        self.assertEqual(workflow.state_of(obj), u'published')

        workflow.transition(obj, request, 'published_to_retracted')
        self.assertEqual(workflow.state_of(obj), u'retracted')

        workflow.initialize(obj)
        workflow.transition(obj, request, 'published_to_voting')
        self.assertEqual(workflow.state_of(obj), u'voting')

        workflow.transition(obj, request, 'voting_to_approved')
        self.assertEqual(workflow.state_of(obj), u'approved')
        
        workflow.transition(obj, request, 'approved_to_finished')
        self.assertEqual(workflow.state_of(obj), u'finished')

        workflow.initialize(obj)
        workflow.transition(obj, request, 'published_to_voting')
        workflow.transition(obj, request, 'voting_to_denied')
        self.assertEqual(workflow.state_of(obj), u'denied')
        
        workflow.transition(obj, request, 'denied_to_finished')
        self.assertEqual(workflow.state_of(obj), u'finished')
        
    def test_poll_states(self):
        xmlconfig.file('voteit/core/workflows/poll.xml', execute=True)
        request = get_current_request()
        
        obj = Poll()
        
        workflow = get_workflow(Poll, Poll.__name__, obj)
        workflow.initialize(obj)
        self.assertEqual(workflow.state_of(obj), u'private')

        workflow.transition(obj, request, 'private_to_ongoing')
        self.assertEqual(workflow.state_of(obj), u'ongoing')

        workflow.transition(obj, request, 'ongoing_to_closed')
        self.assertEqual(workflow.state_of(obj), u'closed')
        
        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_ongoing')
        workflow.transition(obj, request, 'ongoing_to_cancelled')
        self.assertEqual(workflow.state_of(obj), u'cancelled')

        workflow.initialize(obj)
        workflow.transition(obj, request, 'private_to_ongoing')
        workflow.transition(obj, request, 'ongoing_to_private')
        self.assertEqual(workflow.state_of(obj), u'private')
