import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.component import queryUtility
from pyramid.threadlocal import get_current_registry
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.traversal import find_interface
from pyramid_mailer import get_mailer

from voteit.core.models.interfaces import IAgendaItem
from voteit.core import security

admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
participant = set([security.ROLE_PARTICIPANT])
viewer = set([security.ROLE_VIEWER])
voter = set([security.ROLE_VOTER])
owner = set([security.ROLE_OWNER])


class PollTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()
    
    def _make_obj(self):
        """ Poll object need to be in the context of an Agenda Item to work properly
        """
        from voteit.core.models.poll import Poll
        from voteit.core.models.proposal import Proposal
        from voteit.core.models.agenda_item import AgendaItem
        ai = AgendaItem()
        ai['poll'] = Poll()
        
        proposal = Proposal()
        ai['poll'].set_field_value('proposals', set(proposal.uid))

        return ai['poll']
        
    def _register_majority_poll(self, poll):
        from voteit.core.app import register_poll_plugin
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        registry = get_current_registry()
        register_poll_plugin(MajorityPollPlugin, registry=registry)

    def _agenda_item_with_proposals_fixture(self):
        """ Create an agenda item with a poll and two proposals. """
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        agenda_item = AgendaItem()
        agenda_item['prop1'] = Proposal()
        agenda_item['prop2'] = Proposal()
        return agenda_item

    def _make_vote(self, vote_data='hello_world'):
        from voteit.core.models.vote import Vote
        vote = Vote()
        vote.set_vote_data(vote_data)
        return vote

    def test_implements_base_content(self):
        from voteit.core.models.interfaces import IBaseContent
        obj = self._make_obj()
        self.assertTrue(verifyObject(IBaseContent, obj))

    def test_implements_poll(self):
        from voteit.core.models.interfaces import IPoll
        obj = self._make_obj()
        self.assertTrue(verifyObject(IPoll, obj))

    def test_proposal_uids(self):
        """ Proposal uids should be a setable property that connects to
            the dynamic field "proposals".
        """
        obj = self._make_obj()
        obj.proposal_uids = ['hello']
        self.assertEqual(obj.get_field_value('proposals'), ['hello'])
        obj.set_field_value('proposals', ('new', 'uids',))
        self.assertEqual(obj.proposal_uids, ('new', 'uids',))

    def test_poll_plugin_name(self):
        """ poll_plugin_name should get the registered plugins name. """
        obj = self._make_obj()
        obj.set_field_value('poll_plugin', 'my_plugin')
        self.assertEqual(obj.poll_plugin_name, 'my_plugin')
    
    def test_get_proposal_objects(self):
        """ Test that all proposals that belong to this poll gets returned. """
        agenda_item = self._agenda_item_with_proposals_fixture()
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        agenda_item['poll'] = poll = self._make_obj()
        poll.proposal_uids = (prop1.uid, prop2.uid,)
        
        self.assertEqual(set(poll.get_proposal_objects()), set([prop1, prop2,]))
    
    def test_get_all_votes(self):
        """ Get all votes for the current poll. """
        obj = self._make_obj()
        obj['me'] = self._make_vote()
        self.assertEqual(tuple(obj.get_all_votes()), (obj['me'],))

    def test_get_voted_userids(self):
        obj = self._make_obj()
        vote1 = self._make_vote()
        vote1.creators = ['admin']
        vote2 = self._make_vote()
        vote2.creators = ['some_guy']
        obj['vote1'] = vote1
        obj['vote2'] = vote2

        self.assertEqual(obj.get_voted_userids(), frozenset(['admin', 'some_guy']))

    def test_get_voted_userids_bad_vote(self):
        obj = self._make_obj()
        vote1 = self._make_vote()
        obj['v'] = vote1
        self.assertRaises(ValueError, obj.get_voted_userids)

    def test_get_ballots_string(self):
        obj = self._make_obj()
        #Make some default votes
        vote1 = self._make_vote()
        vote2 = self._make_vote()
        obj['vote1'] = vote1
        obj['vote2'] = vote2
        
        #And one other vote
        vote3 = self._make_vote()
        vote3.set_vote_data('other')
        obj['vote3'] = vote3

        obj._calculate_ballots()
        self.assertEqual(obj.ballots, (('hello_world', 2), ('other', 1)))

    def test_ballots_object(self):
        obj = self._make_obj()
        
        #Unique choices
        choice1 = object()
        choice2 = object()

        obj['vote1'] = self._make_vote(choice1)
        obj['vote2'] = self._make_vote(choice1)
        obj['vote3'] = self._make_vote(choice1)
        obj['vote4'] = self._make_vote(choice2)
        obj['vote5'] = self._make_vote(choice2)

        obj._calculate_ballots()

        self.assertEqual(len(obj.ballots), 2)

    def test_ballots_dict(self):
        obj = self._make_obj()
        
        #Unique choices
        choice1 = {'apple':1, 'potato':2}
        choice2 = {'apple':1}

        obj['vote1'] = self._make_vote(choice1)
        obj['vote2'] = self._make_vote(choice1)
        obj['vote3'] = self._make_vote(choice1)
        obj['vote4'] = self._make_vote(choice2)
        obj['vote5'] = self._make_vote(choice2)

        obj._calculate_ballots()
        
        self.assertEqual(obj.ballots, (({'apple': 1}, 2), ({'apple': 1, 'potato': 2}, 3)))

    def _extract_transition_names(self, info):
        return set([x['name'] for x in info])

    def test_poll_transitions(self):
        request = testing.DummyRequest()
        
        #Setup for proper test
        obj = self._make_obj()
        
        ai = find_interface(obj, IAgendaItem)
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')

        self._register_majority_poll(obj)
        obj.set_field_value('poll_plugin', u'majority_poll')
        
        #Initial state
        self.assertEqual(obj.get_workflow_state(), u'private')
        
        #private -> upcoming
        obj.make_workflow_transition(request, 'private_to_upcoming')
        self.assertEqual(obj.get_workflow_state(), u'upcoming')

        #upcoming -> private
        obj.make_workflow_transition(request, 'upcoming_to_private')
        self.assertEqual(obj.get_workflow_state(), u'private')

        #upcoming -> ongoing
        obj.initialize_workflow()
        obj.set_workflow_state(request, 'upcoming')
        obj.make_workflow_transition(request, 'upcoming_to_ongoing')
        self.assertEqual(obj.get_workflow_state(), u'ongoing')

        #upcoming -> canceled
        obj.initialize_workflow()
        obj.set_workflow_state(request, 'upcoming')
        obj.make_workflow_transition(request, 'upcoming_to_canceled')
        self.assertEqual(obj.get_workflow_state(), u'canceled')

        #ongoing -> closed
        obj.initialize_workflow()
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        obj.make_workflow_transition(request, 'ongoing_to_closed')
        self.assertEqual(obj.get_workflow_state(), u'closed')

    def test_available_transitions(self):
        request = testing.DummyRequest()
        
        #Setup for proper test
        obj = self._make_obj()
        
        ai = find_interface(obj, IAgendaItem)
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')

        self._register_majority_poll(obj)
        obj.set_field_value('poll_plugin', u'majority_poll')
        
        #Private - Initial state
        result = self._extract_transition_names(obj.get_available_workflow_states(request))
        self.assertEqual(result, set([u'upcoming']))
        
        #upcoming
        obj.set_workflow_state(request, 'upcoming')
        result = self._extract_transition_names(obj.get_available_workflow_states(request))
        self.assertEqual(result, set([u'private', u'ongoing', u'canceled']))

        #Ongoing
        obj.set_workflow_state(request, 'ongoing')
        result = self._extract_transition_names(obj.get_available_workflow_states(request))
        self.assertEqual(result, set([u'closed']))

        #Canceled
        obj.initialize_workflow()
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'canceled')
        result = self._extract_transition_names(obj.get_available_workflow_states(request))
        self.assertEqual(result, set())

        #Closed
        obj.initialize_workflow()
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        obj.set_workflow_state(request, 'closed')
        result = self._extract_transition_names(obj.get_available_workflow_states(request))
        self.assertEqual(result, set())
        

    def test_workflow_state_to_ongoing(self):
        """ When you try to set state to ongoing on poll and 
            agenda item is not ongoing an exception should be raised.
        """
        request = testing.DummyRequest()
        
        obj = self._make_obj()
        
        obj.set_workflow_state(request, 'upcoming')
        self.assertRaises(Exception, obj.set_workflow_state, 'ongoing')
        
        ai = find_interface(obj, IAgendaItem)
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        
        obj.set_workflow_state(request, 'ongoing')

    def test_ongoing_wo_proposal(self):
        request = testing.DummyRequest()
        poll = self._make_obj()
        
        ai = find_interface(poll, IAgendaItem)
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        
        # remove all proposals on poll
        poll.set_field_value('proposals', set())

        poll.set_workflow_state(request, 'upcoming')
        
        self.assertRaises(ValueError, poll.set_workflow_state, request, 'ongoing')

    def test_email_voters_about_ongoing_poll(self):
        #FIXME: Parts of this test should be turned into a site fixture that can be reusable
        from voteit.core.bootstrap import bootstrap_voteit
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.poll import Poll
        from voteit.core.security import authn_policy
        from voteit.core.security import authz_policy
        from voteit.core.security import unrestricted_wf_transition_to
        
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request, registry=self.config.registry)
        self.config.setup_registry(authentication_policy=authn_policy,
                                   authorization_policy=authz_policy)
        self.config.include('pyramid_mailer.testing')
        self.config.scan('voteit.core.subscribers.poll')
        
        self.config.scan('voteit.core.models.meeting')
        self.config.scan('voteit.core.models.site')
        self.config.scan('voteit.core.models.user')
        self.config.scan('voteit.core.models.users')
        
        mailer = get_mailer(request)

        root = bootstrap_voteit(echo=False)
        root['users']['admin'].set_field_value('email', 'this@that.com')
        
        meeting = root['meeting'] = Meeting()
        meeting.add_groups('admin', [security.ROLE_VOTER])
        unrestricted_wf_transition_to(meeting, 'ongoing')
        
        meeting['ai'] = self._agenda_item_with_proposals_fixture()
        ai = meeting['ai']
        unrestricted_wf_transition_to(ai, 'upcoming')
        unrestricted_wf_transition_to(ai, 'ongoing')
        
        ai['poll'] = Poll()
        poll = ai['poll']
        poll.set_field_value('proposals', set([ai['prop1'].uid, ai['prop2'].uid]))
        unrestricted_wf_transition_to(poll, 'upcoming')

        #Okay, so this is the actual test...
        self.assertEqual(len(mailer.outbox), 0)
        unrestricted_wf_transition_to(poll, 'ongoing')
        self.assertEqual(len(mailer.outbox), 1)
        self.failUnless('this@that.com' in mailer.outbox[0].recipients)


class PollPermissionTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        # load workflow
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        """ Poll object need to be in the context of an Agenda Item to work properly
        """
        from voteit.core.models.poll import Poll
        poll = Poll()
        
        from voteit.core.models.proposal import Proposal
        proposal = Proposal()
        poll.set_field_value('proposals', set(proposal.uid))
        
        from voteit.core.models.agenda_item import AgendaItem
        ai = AgendaItem()
        ai['poll'] = poll

        return poll

    def _register_majority_poll(self, poll):
        from voteit.core.app import register_poll_plugin
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        registry = get_current_registry()
        register_poll_plugin(MajorityPollPlugin, registry=registry)
        poll.set_field_value('poll_plugin', u'majority_poll')

    def test_private(self):
        poll = self._make_obj()
        
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator)
        
        self.assertEqual(self.pap(poll, security.EDIT), admin | moderator)
        
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())

        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_upcoming(self):
        poll = self._make_obj()
        request = testing.DummyRequest()
        poll.set_workflow_state(request, 'upcoming')
        
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | participant | viewer | voter)
        
        self.assertEqual(self.pap(poll, security.EDIT), admin | moderator)
        
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())

        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_ongoing(self):
        request = testing.DummyRequest()
        poll = self._make_obj()
        ai = find_interface(poll, IAgendaItem)
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        poll.set_workflow_state(request, 'upcoming')
        poll.set_workflow_state(request, 'ongoing')
        
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | participant | viewer | voter)
        
        self.assertEqual(self.pap(poll, security.EDIT), set())
        
        self.assertEqual(self.pap(poll, security.DELETE), set())
        
        self.assertEqual(self.pap(poll, security.ADD_VOTE), voter)

        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)
        
    def test_closed_or_canceled(self):
        request = testing.DummyRequest()
        poll = self._make_obj()
        ai = find_interface(poll, IAgendaItem)
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        self._register_majority_poll(poll)
        poll.set_workflow_state(request, 'upcoming')
        poll.set_workflow_state(request, 'ongoing')
        poll.set_workflow_state(request, 'closed')
        
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | participant | viewer | voter)
        
        self.assertEqual(self.pap(poll, security.EDIT), set())
        
        self.assertEqual(self.pap(poll, security.DELETE), set())
        
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())
