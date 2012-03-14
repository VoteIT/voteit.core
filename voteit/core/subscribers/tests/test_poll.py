import unittest

from pyramid import testing
from zope.component.event import objectEventNotify

from voteit.core.events import ObjectUpdatedEvent
from voteit.core.security import unrestricted_wf_transition_to
from voteit.core.testing_helpers import register_workflows
from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_security_policies


class PollTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.scan('voteit.core.subscribers.poll')

    def tearDown(self):
        testing.tearDown()

    def test_change_states_proposals(self):
        register_workflows(self.config)
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)

        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        ai = AgendaItem()
        ai['prop1'] = Proposal()
        ai['prop2'] = Proposal()
        
        from voteit.core.models.poll import Poll
        ai['poll'] = Poll()
        ai['poll'].proposal_uids = (ai['prop1'].uid, ai['prop2'].uid)
        
        ai['poll'].set_workflow_state(request, 'upcoming')
        
        # reset state of proposals to published so that we actually test the subscriber
        ai['prop1'].set_workflow_state(request, 'published')
        ai['prop2'].set_workflow_state(request, 'published')
        
        objectEventNotify(ObjectUpdatedEvent(ai['poll'], None, 'dummy'))
        
        self.assertEqual(ai['prop1'].get_workflow_state(), 'voting')
        self.assertEqual(ai['prop2'].get_workflow_state(), 'voting')

    def test_reset_unread_on_state_change(self):
        root = bootstrap_and_fixture(self.config)
        register_workflows(self.config)
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)
        
        
        
        register_security_policies(self.config)
        
        self.config.testing_securitypolicy(userid='admin',
                                           permissive=True)
        
        from voteit.core.models.meeting import Meeting
        meeting = root['meeting'] = Meeting()

        from voteit.core.security import ROLE_ADMIN, ROLE_VOTER
        meeting.add_groups('admin', [ROLE_ADMIN, ROLE_VOTER])
        
        meeting.set_workflow_state(request, 'ongoing')

        from voteit.core.models.agenda_item import AgendaItem
        ai = meeting['ai'] = AgendaItem()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        
        from voteit.core.models.proposal import Proposal
        ai['prop1'] = Proposal()
        ai['prop2'] = Proposal()

        self.config.include('voteit.core.models.unread')
        self.config.scan('voteit.core.subscribers.poll')
        
        from voteit.core.models.poll import Poll
        poll = ai['poll'] = Poll()
        poll.proposal_uids = (ai['prop1'].uid, ai['prop2'].uid)
        
        poll.set_workflow_state(request, 'upcoming')
        
        from voteit.core.models.unread import Unread
        obj = Unread(poll)
        
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin',)))
        
        obj.mark_as_read('admin')
        
        self.assertEqual(obj.get_unread_userids(), frozenset(()))
        
        poll.set_workflow_state(request, 'upcoming')
        
        self.assertEqual(obj.get_unread_userids(), frozenset(('admin',)))