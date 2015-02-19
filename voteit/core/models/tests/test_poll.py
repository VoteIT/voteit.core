import unittest
from datetime import datetime

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.traversal import find_interface
from pyramid_mailer import get_mailer
from pyramid.security import Authenticated
from pyramid.httpexceptions import HTTPForbidden

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.poll_plugin import PollPlugin
from voteit.core import security
from voteit.core.testing_helpers import active_poll_fixture
from voteit.core.testing_helpers import register_workflows


admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
authenticated = set([Authenticated])
discuss = set([security.ROLE_DISCUSS])
propose = set([security.ROLE_PROPOSE])
viewer = set([security.ROLE_VIEWER])
voter = set([security.ROLE_VOTER])
owner = set([security.ROLE_OWNER])


class PollTests(unittest.TestCase):
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
        self.config.include('voteit.core.models.flash_messages')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.poll import Poll
        return Poll

    def _make_obj(self):
        """ Poll object need to be in the context of an Agenda Item to work properly
        """
        from voteit.core.models.proposal import Proposal
        from voteit.core.models.agenda_item import AgendaItem
        ai = AgendaItem()
        ai['poll'] = self._cut()
        proposal = Proposal()
        ai['poll'].set_field_value('proposals', set(proposal.uid))
        return ai['poll']

    def _register_majority_poll(self, poll):
        self.config.include('voteit.core.plugins.majority_poll')
        poll.set_field_value('poll_plugin', u'majority_poll')

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

    def test_verify_class(self):
        self.assertTrue(verifyClass(IPoll, self._cut))

    def test_verify_object(self):
        self.assertTrue(verifyObject(IPoll, self._cut()))

    def test_proposal_uids(self):
        """ Proposal uids should be a setable property that connects to
            the dynamic field "proposals".
        """
        obj = self._make_obj()
        obj.proposal_uids = ['hello']
        self.assertEqual(obj.get_field_value('proposals'), ('hello',))
        obj.set_field_value('proposals', ('new', 'uids',))
        self.assertEqual(obj.proposal_uids, ('new', 'uids',))

    def test_start_time_property(self):
        now = datetime.now()
        obj = self._cut(start_time = now)
        self.assertEqual(obj.start_time, now)

    def test_end_time_property(self):
        now = datetime.now()
        obj = self._cut(end_time = now)
        self.assertEqual(obj.end_time, now)

    def test_poll_settings_property(self):
        settings = {'this': 1, 'other': 2}
        obj = self._cut()
        obj.poll_settings = settings
        self.assertEqual(obj.poll_settings, settings)

    def test_poll_settings_property_bad_type(self):
        settings = "Hello!"
        obj = self._cut()
        try:
            obj.poll_settings = settings
            self.fail("poll_settings attr shouldn't be anything else than a string")
        except TypeError:
            pass

    def test_poll_plugin_name(self):
        """ poll_plugin_name should get the registered plugins name. """
        obj = self._cut()
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

    def test_get_proposal_objects_wrong_context(self):
        obj = self._cut()
        self.assertRaises(ValueError, obj.get_proposal_objects)

    def test_get_all_votes(self):
        """ Get all votes for the current poll. """
        obj = self._cut()
        obj['me'] = self._make_vote()
        self.assertEqual(tuple(obj.get_all_votes()), (obj['me'],))

    def test_get_voted_userids(self):
        obj = self._make_obj()
        vote1 = self._make_vote()
        vote2 = self._make_vote()
        obj['vote1'] = vote1
        obj['vote2'] = vote2
        self.assertEqual(obj.get_voted_userids(), frozenset(['vote1', 'vote2']))

    def test_close_poll(self):
        register_workflows(self.config)
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)
        agenda_item = self._agenda_item_with_proposals_fixture()
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        agenda_item['poll'] = poll = self._cut()
        poll.proposal_uids = (prop1.uid, prop2.uid,)

        class _MockPollPlugin(PollPlugin):
            def handle_close(self):
                pass
            def change_states_of(self):
                return {prop1.uid: 'voting', prop2.uid:'voting'}

        self.config.registry.registerAdapter(_MockPollPlugin, (IPoll,), IPollPlugin, 'mock_poll_plugin')
        poll.set_field_value('poll_plugin', 'mock_poll_plugin')
        poll.close_poll()
        #Should have been adjusted if everything went according to plan
        self.assertEqual(prop2.get_workflow_state(), 'voting')

    def test_adjust_proposal_states_bad_uids(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)
        poll = self._cut()
        self.assertRaises(ValueError, poll.adjust_proposal_states, {'bad_uid': 'state'})

    def test_adjust_proposal_states(self):
        register_workflows(self.config)
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)
        agenda_item = self._agenda_item_with_proposals_fixture()
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        prop1.set_workflow_state(request, 'voting')
        prop2.set_workflow_state(request, 'voting')
        agenda_item['poll'] = poll = self._cut()
        poll.proposal_uids = (prop1.uid, prop2.uid,)
        adjust_states = {prop1.uid: 'denied',
                         prop2.uid: 'approved',}
        poll.adjust_proposal_states(adjust_states)
        self.assertEqual(prop1.get_workflow_state(), 'denied')
        self.assertEqual(prop2.get_workflow_state(), 'approved')

    def test_adjust_proposal_states_already_correct_state(self):
        register_workflows(self.config)
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)
        agenda_item = self._agenda_item_with_proposals_fixture()
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        prop1.set_workflow_state(request, 'voting')
        prop2.set_workflow_state(request, 'voting')
        prop2.set_workflow_state(request, 'approved')
        agenda_item['poll'] = poll = self._cut()
        poll.proposal_uids = (prop1.uid, prop2.uid,)
        adjust_states = {prop1.uid: 'denied',
                         prop2.uid: 'approved',}
        poll.adjust_proposal_states(adjust_states)
        self.assertEqual(prop1.get_workflow_state(), 'denied')
        #No change here, but no exception raised either
        self.assertEqual(prop2.get_workflow_state(), 'approved')

    def test_adjust_proposal_states_bad_state(self):
        register_workflows(self.config)
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)
        agenda_item = self._agenda_item_with_proposals_fixture()
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        agenda_item['poll'] = poll = self._cut()
        poll.proposal_uids = (prop1.uid, prop2.uid,)
        adjust_states = {prop1.uid: 'john',
                         prop2.uid: 'doe',}
        poll.adjust_proposal_states(adjust_states)
        self.assertEqual(prop1.get_workflow_state(), 'published')
        self.assertEqual(prop2.get_workflow_state(), 'published')

    def test_get_ballots_string(self):
        obj = self._cut()
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

    def test_ballots_dict(self):
        obj = self._cut()
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

    def test_workflow_state_to_ongoing(self):
        """ When you try to set state to ongoing on poll and 
            agenda item is not ongoing an exception should be raised.
        """
        register_workflows(self.config)
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'upcoming')
        self.assertRaises(Exception, obj.set_workflow_state, 'ongoing')
        ai = find_interface(obj, IAgendaItem)
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        obj.set_workflow_state(request, 'ongoing')

    def test_ongoing_wo_proposal(self):
        register_workflows(self.config)
        poll = self._make_obj()
        ai = find_interface(poll, IAgendaItem)
        security.unrestricted_wf_transition_to(ai, 'upcoming')
        security.unrestricted_wf_transition_to(ai, 'ongoing')
        # remove all proposals on poll
        poll.set_field_value('proposals', set())
        security.unrestricted_wf_transition_to(poll, 'upcoming')
        request = testing.DummyRequest()
        self.assertRaises(HTTPForbidden, poll.set_workflow_state, request, 'ongoing')

    def test_render_poll_result(self):
        #note: This shouldn't test the template since that's covered by each plugin
        request = testing.DummyRequest()
        poll = self._cut()
        _marker = object()

        from voteit.core.views.api import APIView
        api = APIView(poll, request)

        class _MockPollPlugin(PollPlugin):
            def render_result(self, request, api, complete=True):
                return _marker

        self.config.registry.registerAdapter(_MockPollPlugin, (IPoll,), IPollPlugin, 'mock_poll_plugin')
        poll.set_field_value('poll_plugin', 'mock_poll_plugin')
        self.assertEqual(poll.render_poll_result(request, api), _marker)

    def test_get_proposal_by_uid(self):
        agenda_item = self._agenda_item_with_proposals_fixture()
        uid = agenda_item['prop1'].uid
        agenda_item['poll'] = poll = self._cut()
        poll.proposal_uids = (uid,)
        prop = poll.get_proposal_by_uid(uid)
        self.assertEqual(prop, agenda_item['prop1'])
        
    def test_get_proposal_by_uid_non_existing_uid(self):
        agenda_item = self._agenda_item_with_proposals_fixture()
        uid = agenda_item['prop1'].uid
        agenda_item['poll'] = poll = self._cut()
        self.assertRaises(KeyError, poll.get_proposal_by_uid, uid)


class PollMethodsTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('voteit.core.models.flash_messages')
        self.config.include('pyramid_chameleon')

    def tearDown(self):
        testing.tearDown()

    def test_email_voters_about_ongoing_poll(self):
        root = active_poll_fixture(self.config)
        self.config.testing_securitypolicy('userid', permissive = True)
        poll = root['meeting']['ai']['poll']
        request = testing.DummyRequest()
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 0)
        security.unrestricted_wf_transition_to(poll, 'ongoing')
        self.assertEqual(len(mailer.outbox), 1)
        self.failUnless('this@that.com' in mailer.outbox[0].recipients)

    def test_ongoing_poll_callback_agenda_item_not_ongoing_error(self):
        root = active_poll_fixture(self.config)
        ai = root['meeting']['ai']
        security.unrestricted_wf_transition_to(ai, 'upcoming')
        self.assertRaises(HTTPForbidden, security.unrestricted_wf_transition_to, ai['poll'], 'ongoing')


class PollPermissionTests(unittest.TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
        self.config.include('arche.testing')
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        register_workflows(self.config)
        self.config.include('voteit.core.models.flash_messages')
        self.config.include('voteit.core.models.poll')

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
        self.config.include('voteit.core.plugins.majority_poll')
        poll.set_field_value('poll_plugin', u'majority_poll')

    def test_private(self):
        poll = self._make_obj()
        
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator)
        self.assertEqual(self.pap(poll, security.EDIT), admin | moderator)
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())
        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_upcoming_w_ongoing_ai(self):
        poll = self._make_obj()
        request = testing.DummyRequest()
        poll.__parent__.set_workflow_state(request, 'upcoming')
        poll.set_workflow_state(request, 'upcoming')
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(poll, security.EDIT), admin | moderator)
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())
        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_upcoming_w_private_ai(self):
        poll = self._make_obj()
        request = testing.DummyRequest()
        security.unrestricted_wf_transition_to(poll, 'upcoming')
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator )
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
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(poll, security.EDIT), set())
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(poll, security.ADD_VOTE), voter)
        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)
        
    def test_closed(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)
        poll = self._make_obj()
        ai = find_interface(poll, IAgendaItem)
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        self._register_majority_poll(poll)
        poll.set_workflow_state(request, 'upcoming')
        poll.set_workflow_state(request, 'ongoing')
        poll.set_workflow_state(request, 'closed')
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(poll, security.EDIT), set())
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())
        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), set())

    def test_canceled(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(registry = self.config.registry, request = request)
        poll = self._make_obj()
        ai = find_interface(poll, IAgendaItem)
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        self._register_majority_poll(poll)
        poll.set_workflow_state(request, 'upcoming')
        poll.set_workflow_state(request, 'ongoing')
        poll.set_workflow_state(request, 'canceled')
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(poll, security.EDIT), set())
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())
        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)
