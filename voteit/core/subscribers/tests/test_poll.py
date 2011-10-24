import unittest

from pyramid import testing

from voteit.core.testing_helpers import register_workflows


class PollTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

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
        
        self.assertEqual(ai['prop1'].get_workflow_state(), 'voting')
        self.assertEqual(ai['prop2'].get_workflow_state(), 'voting')
