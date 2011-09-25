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
from voteit.core.models.interfaces import IMeeting, IInviteTicket
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IPoll

#FIXME: Refactor and add under each content type

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()
        
    def test_verify_workflow(self):
        workflow = get_workflow(SiteRoot, SiteRoot.__name__)
        self.assertEqual(workflow, None)
        
        workflow = get_workflow(IMeeting, 'Meeting')
        self.assertEqual(workflow.name, u'Meeting Workflow')
        
        workflow = get_workflow(IAgendaItem, 'AgendaItem')
        self.assertEqual(workflow.name, u'Agenda Item Workflow')
        
        workflow = get_workflow(IProposal, 'Proposal')
        self.assertEqual(workflow.name, u'Proposal Workflow')
        
        workflow = get_workflow(IPoll, 'Poll')
        self.assertEqual(workflow.name, u'Poll Workflow')

        workflow = get_workflow(IInviteTicket, 'InviteTicket')
        self.failUnless(workflow)
        
    def test_meeting_states(self):
        obj = Meeting()
        request = testing.DummyRequest()

        self.assertEqual(obj.get_workflow_state(), u'upcoming')

        obj.make_workflow_transition(request, 'upcoming_to_ongoing')
        self.assertEqual(obj.get_workflow_state(), u'ongoing')

        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'upcoming_to_closed')
        self.assertEqual(obj.get_workflow_state(), u'closed')

        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'upcoming_to_ongoing')
        obj.make_workflow_transition(request, 'ongoing_to_upcoming')
        self.assertEqual(obj.get_workflow_state(), u'upcoming')

        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'upcoming_to_ongoing')
        obj.make_workflow_transition(request, 'ongoing_to_closed')
        self.assertEqual(obj.get_workflow_state(), u'closed')
        
        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'upcoming_to_closed')
        obj.make_workflow_transition(request, 'closed_to_ongoing')
        self.assertEqual(obj.get_workflow_state(), u'ongoing')
        
        
    def test_agenda_item_states(self):
        obj = AgendaItem()
        request = testing.DummyRequest()

        workflow = get_workflow(AgendaItem, AgendaItem.__name__, obj)
        obj.initialize_workflow()
        self.assertEqual(obj.get_workflow_state(), u'private')

        obj.make_workflow_transition(request, 'private_to_upcoming')
        self.assertEqual(obj.get_workflow_state(), u'upcoming')

        obj.make_workflow_transition(request, 'upcoming_to_ongoing')
        self.assertEqual(obj.get_workflow_state(), u'ongoing')

        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'private_to_upcoming')
        obj.make_workflow_transition(request, 'upcoming_to_closed')
        self.assertEqual(obj.get_workflow_state(), u'closed')

        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'private_to_upcoming')
        obj.make_workflow_transition(request, 'upcoming_to_ongoing')
        obj.make_workflow_transition(request, 'ongoing_to_upcoming')
        self.assertEqual(obj.get_workflow_state(), u'upcoming')

        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'private_to_upcoming')
        obj.make_workflow_transition(request, 'upcoming_to_ongoing')
        obj.make_workflow_transition(request, 'ongoing_to_closed')
        self.assertEqual(obj.get_workflow_state(), u'closed')
        
        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'private_to_upcoming')
        obj.make_workflow_transition(request, 'upcoming_to_closed')
        obj.make_workflow_transition(request, 'closed_to_ongoing')
        self.assertEqual(obj.get_workflow_state(), u'ongoing')
        
        
    def test_proposal_states(self):
        obj = Proposal()
        request = testing.DummyRequest()
        
        self.assertEqual(obj.get_workflow_state(), u'published')

        obj.make_workflow_transition(request, 'published_to_retracted')
        self.assertEqual(obj.get_workflow_state(), u'retracted')

        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'published_to_voting')
        self.assertEqual(obj.get_workflow_state(), u'voting')

        obj.make_workflow_transition(request, 'voting_to_approved')
        self.assertEqual(obj.get_workflow_state(), u'approved')

        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'published_to_unhandled')
        self.assertEqual(obj.get_workflow_state(), u'unhandled')

        obj.initialize_workflow()
        obj.make_workflow_transition(request, 'published_to_voting')
        obj.make_workflow_transition(request, 'voting_to_denied')
        self.assertEqual(obj.get_workflow_state(), u'denied')
