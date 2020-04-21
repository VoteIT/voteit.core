import unittest

from pyramid import testing
from pyramid.exceptions import HTTPForbidden

from voteit.core import security
from voteit.core.testing_helpers import register_workflows
from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import active_poll_fixture


class PollTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_chameleon')
        self.config.include('arche.testing.catalog')
        self.root = bootstrap_and_fixture(self.config)

    def tearDown(self):
        testing.tearDown()

    def test_change_states_proposals(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        from voteit.core.models.poll import Poll
        register_workflows(self.config)
        request = testing.DummyRequest()
        self.config.begin(request)
        self.root['ai'] = ai = AgendaItem()
        ai['prop1'] = Proposal()
        ai['prop2'] = Proposal()
        ai['poll'] = Poll()
        ai['poll'].proposal_uids = (ai['prop1'].uid, ai['prop2'].uid)
        ai['poll'].set_workflow_state(request, 'upcoming')
        self.assertEqual(ai['prop1'].get_workflow_state(), 'voting')
        self.assertEqual(ai['prop2'].get_workflow_state(), 'voting')

    def test_proposal_in_wrong_state(self):
        register_workflows(self.config)
        request = testing.DummyRequest()
        self.config.begin(request)
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        from voteit.core.models.poll import Poll
        self.root['ai'] = ai = AgendaItem()
        ai['prop'] = Proposal()
        ai['poll'] = Poll()
        ai['poll'].proposal_uids = (ai['prop'].uid, )
        self.config.include('voteit.core.subscribers.poll')
        #Set state to something that doesn't have a transition to 'voting'
        ai['prop'].set_workflow_state(request, 'denied')
        self.assertRaises(HTTPForbidden, ai['poll'].set_workflow_state, request, 'upcoming')


class PollActiveTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_chameleon')
        self.config.include('arche.testing.catalog')

    def tearDown(self):
        testing.tearDown()

    def test_closed_saves_voters(self):
        self.config.include('voteit.core.plugins.majority_poll')
        root = _voters_fixture(self.config)
        self.config.include('arche.testing.setup_auth')
        self.config.include('voteit.core.security')
        root['meeting'].del_groups('admin', [security.ROLE_VOTER])
        poll = root['meeting']['ai']['poll']
        poll.set_field_value('poll_plugin', 'majority_poll')
        security.unrestricted_wf_transition_to(poll, 'ongoing')
        security.unrestricted_wf_transition_to(poll, 'closed')
        self.assertEqual(poll.get_field_value('voters_mark_closed'), frozenset(['alice', 'ben', 'celine']))

    def test_ongoing_saves_voters(self):
        self.config.include('arche.testing')
        self.config.include('voteit.core.models.meeting')
        root = _voters_fixture(self.config)
        self.config.include('arche.testing.setup_auth')
        self.config.include('voteit.core.subscribers.poll')
        self.config.include('voteit.core.security')
        poll = root['meeting']['ai']['poll']
        security.unrestricted_wf_transition_to(poll, 'ongoing')
        self.assertEqual(poll.get_field_value('voters_mark_ongoing'), frozenset(['alice', 'ben', 'celine', 'admin']))

    def test_poll_is_deleted(self):
        self.config.include('voteit.core.plugins.majority_poll')
        request = testing.DummyRequest()
        self.config.begin(request)
        root = active_poll_fixture(self.config)
        self.config.testing_securitypolicy(userid='mr_tester')
        meeting = root['meeting']
        ai = meeting['ai']
        poll = ai['poll']
        poll.poll_plugin_name = "majority_poll"
        poll.set_workflow_state(request, 'ongoing')
        # making sure that proposals are in voting state after poll is set to ongoing
        self.assertEqual(ai['prop1'].get_workflow_state(), 'voting')
        self.assertEqual(ai['prop2'].get_workflow_state(), 'voting')
        self.config.include('voteit.core.subscribers.poll')
        del ai['poll']
        self.assertEqual(ai['prop1'].get_workflow_state(), 'published')
        self.assertEqual(ai['prop2'].get_workflow_state(), 'published')


def _voters_fixture(config):
    from voteit.core.models.user import User
    root = active_poll_fixture(config)
    for userid in ('alice', 'ben', 'celine'):
        root.users[userid] = User()
        root['meeting'].add_groups(userid, [security.ROLE_VOTER])
    return root
