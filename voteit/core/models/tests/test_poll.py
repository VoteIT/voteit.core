import unittest
from datetime import datetime, timedelta

from BTrees.OOBTree import OOBTree
from arche.resources import User
from arche.testing import barebone_fixture
from arche.utils import utcnow
from pyramid import testing
from voteit.core.security import ROLE_VOTER
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
from voteit.core.testing_helpers import active_poll_fixture, bootstrap_and_fixture


admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
authenticated = set([Authenticated])
discuss = set([security.ROLE_DISCUSS])
propose = set([security.ROLE_PROPOSE])
viewer = set([security.ROLE_VIEWER])
voter = set([security.ROLE_VOTER])
owner = set([security.ROLE_OWNER])


def poll_fixture():
    from voteit.core.models.poll import Poll
    from voteit.core.models.meeting import Meeting
    from voteit.core.models.agenda_item import AgendaItem
    from voteit.core.models.proposal import Proposal

    root = barebone_fixture()
    root['users']['admin'] = User(email='this@that.com')
    meeting = root['m'] = Meeting()
    meeting.local_roles.add('admin', [ROLE_VOTER])
    ai = meeting['ai'] = AgendaItem()
    ai['prop1'] = Proposal(text = "Proposal 1", uid="p1")
    ai['prop2'] = Proposal(text = "Proposal 2", uid="p2")
    ai['poll'] = poll = Poll(title = 'A poll')
    poll.update(proposals = ["p2", "p1"])
    return root
    #poll = ai['poll']
    #poll.set_field_value('proposals', set([ai['prop1'].uid, ai['prop2'].uid]))
    #poll.set_workflow_state(request, 'upcoming')

    #root = bootstrap_and_fixture(config)
    #request = testing.DummyRequest()
    #root['users']['admin'].set_field_value('email', 'this@that.com')
    #meeting.set_workflow_state(request, 'ongoing')
    #ai = meeting['ai'] = AgendaItem()

    #ai.set_workflow_state(request, 'upcoming')
    #ai.set_workflow_state(request, 'ongoing')
    #ai['poll'] = Poll(title = 'A poll')
    #poll = ai['poll']
    #poll.set_field_value('proposals', set([ai['prop1'].uid, ai['prop2'].uid]))
    #poll.set_workflow_state(request, 'upcoming')
    #return root


    ###
    # config = testing.setUp(request = request, registry = config.registry)
    #config.include('pyramid_mailer.testing')
    #config.include('voteit.core.subscribers.poll')


class PollTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing')

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
        poll.set_field_value('poll_plugin', 'majority_poll')

    #def _agenda_item_with_proposals_fixture(self):
    #    """ Create an agenda item with a poll and two proposals. """
    #    from voteit.core.models.agenda_item import AgendaItem
    #    from voteit.core.models.proposal import Proposal
    #    root = bootstrap_and_fixture(self.config)
    #    root['ai'] = agenda_item = AgendaItem()
    #    agenda_item['prop1'] = Proposal()
    #    agenda_item['prop2'] = Proposal()
    #    return agenda_item

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
        self.assertEqual(obj.proposals, ('hello',))
        obj.proposals = {'new', 'uids'}
        self.assertEqual(obj.proposal_uids, ('new', 'uids',))

    def test_poll_settings_property(self):
        settings = {'this': 1, 'other': 2}
        obj = self._cut()
        obj.poll_settings = settings
        self.assertEqual(dict(obj.poll_settings), settings)
        self.assertIsInstance(obj.poll_settings, OOBTree)

    def test_poll_settings_property_bad_type(self):
        settings = "Hello!"
        obj = self._cut()
        try:
            obj.poll_settings = settings
            self.fail("poll_settings attr shouldn't be anything else than a string")
        except TypeError:
            pass

    def test_get_proposal_objects(self):
        """ Test that all proposals that belong to this poll gets returned. """
        self.config.include('voteit.core.testing_helpers.register_catalog')
        root = poll_fixture()
        agenda_item = root['m']['ai']
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        poll = agenda_item['poll']
        #agenda_item['poll'] = poll = self._cut(proposals=[prop1.uid, prop2.uid])
        self.assertEqual(set(poll.get_proposal_objects()), set([prop1, prop2,]))

    def _ordering_fixture(self):
        self.config.include('voteit.core.testing_helpers.register_catalog')
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = barebone_fixture()
        root['m'] = m = Meeting()
        m['ai'] = ai = AgendaItem()
        now = utcnow()
        ai['p1'] = Proposal(created=now, text='Abc', uid='a')
        ai['p2'] = Proposal(created=now+timedelta(seconds=2), text='aa', uid='b')
        ai['p3'] = Proposal(created=now+timedelta(seconds=4), text='cc', uid='c')
        ai['p4'] = Proposal(created=now+timedelta(seconds=6), text='zz', uid='d')
        ai['p5'] = Proposal(created=now+timedelta(seconds=8), text='C', uid='e')
        ai['poll'] = self._cut(proposals=['a', 'b', 'c', 'd', 'e'])
        return root

    def test_get_proposal_objects_ordering_chronological(self):
        root = self._ordering_fixture()
        poll = root['m']['ai']['poll']
        #Chronological order is default
        self.assertEqual([x.uid for x in poll.get_proposal_objects()], ['a', 'b', 'c', 'd', 'e'])

    def test_get_proposal_objects_ordering_random(self):
        from voteit.core.models.poll import PROPOSAL_ORDER_RANDOM
        root = self._ordering_fixture()
        root['m'].poll_proposals_default_order = PROPOSAL_ORDER_RANDOM
        poll = root['m']['ai']['poll']
        r = {}
        for i in range(5):
            r[i] = [x.uid for x in poll.get_proposal_objects()]
        self.failIf(r[0] == r[1] == r[2] == r[3] == r[4])

    def test_get_proposal_objects_ordering_alphabetical(self):
        from voteit.core.models.poll import PROPOSAL_ORDER_ALPHABETICAL
        root = self._ordering_fixture()
        root['m'].poll_proposals_default_order = PROPOSAL_ORDER_ALPHABETICAL
        poll = root['m']['ai']['poll']
        self.assertEqual([x.uid for x in poll.get_proposal_objects()], ['b', 'a', 'e', 'c', 'd'])

    def test_get_proposal_objects_local_setting(self):
        from voteit.core.models.poll import PROPOSAL_ORDER_ALPHABETICAL
        from voteit.core.models.poll import PROPOSAL_ORDER_CHRONOLOGICAL
        root = self._ordering_fixture()
        root['m'].poll_proposals_default_order = PROPOSAL_ORDER_CHRONOLOGICAL
        poll = root['m']['ai']['poll']
        poll.proposal_order = PROPOSAL_ORDER_ALPHABETICAL
        # Alphabetical order overrides
        self.assertEqual([x.uid for x in poll.get_proposal_objects()], ['b', 'a', 'e', 'c', 'd'])

    def test_get_proposal_objects_wrong_context(self):
        obj = self._cut()
        self.assertRaises(ValueError, obj.get_proposal_objects)

    def test_close_poll(self):
        self.config.include('voteit.core.testing_helpers.register_catalog')
        self.config.include('voteit.core.testing_helpers.register_workflows')
        request = testing.DummyRequest()
        self.config.begin(request)
        root = poll_fixture()
        agenda_item = root['m']['ai']
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        poll = agenda_item['poll']

        class _MockPollPlugin(PollPlugin):
            def handle_close(self):
                pass
            def change_states_of(self):
                return {prop1.uid: 'voting', prop2.uid:'voting'}

        self.config.registry.registerAdapter(_MockPollPlugin, (IPoll,), IPollPlugin, 'mock_poll_plugin')
        poll.poll_plugin = 'mock_poll_plugin'
        poll.close_poll()
        #Should have been adjusted if everything went according to plan
        self.assertEqual(prop2.wf_state, 'voting')

    def test_adjust_proposal_states_bad_uids(self):
        request = testing.DummyRequest()
        self.config.begin(request)
        poll = self._cut()
        self.assertRaises(ValueError, poll.adjust_proposal_states, {'bad_uid': 'state'})

    def test_adjust_proposal_states(self):
        self.config.include('voteit.core.testing_helpers.register_catalog')
        self.config.include('voteit.core.testing_helpers.register_workflows')
        root = poll_fixture()
        agenda_item = root['m']['ai']
        request = testing.DummyRequest()
        self.config.begin(request)
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        prop1.workflow.do_transition('voting', request, force=True)
        prop2.workflow.do_transition('voting', request, force=True)
        adjust_states = {prop1.uid: 'denied',
                         prop2.uid: 'approved',}
        poll = agenda_item['poll']
        poll.adjust_proposal_states(adjust_states)
        self.assertEqual(prop1.get_workflow_state(), 'denied')
        self.assertEqual(prop2.get_workflow_state(), 'approved')

    def test_adjust_proposal_states_already_correct_state(self):
        self.config.include('voteit.core.testing_helpers.register_workflows')
        self.config.include('voteit.core.testing_helpers.register_catalog')
        request = testing.DummyRequest()
        self.config.begin(request)
        root = poll_fixture()
        agenda_item = root['m']['ai']
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        prop1.workflow.do_transition('voting', request, force=True)
        prop2.workflow.do_transition('approved', request, force=True)
        poll = agenda_item['poll']
        adjust_states = {prop1.uid: 'denied',
                         prop2.uid: 'approved',}
        poll.adjust_proposal_states(adjust_states)
        self.assertEqual(prop1.wf_state, 'denied')
        #No change here, but no exception raised either
        self.assertEqual(prop2.wf_state, 'approved')

    def test_adjust_proposal_states_bad_state(self):
        self.config.include('voteit.core.testing_helpers.register_workflows')
        self.config.include('voteit.core.testing_helpers.register_catalog')
        request = testing.DummyRequest()
        self.config.begin(request)
        root = poll_fixture()
        agenda_item = root['m']['ai']
        prop1 = agenda_item['prop1']
        prop2 = agenda_item['prop2']
        poll = agenda_item['poll']
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
        ballots = obj.calculate_ballots()
        self.assertEqual(ballots, (('hello_world', 2), ('other', 1)))

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
        ballots = obj.calculate_ballots()
        self.assertEqual(ballots, (({'apple': 1}, 2), ({'apple': 1, 'potato': 2}, 3)))

    def test_workflow_state_to_ongoing(self):
        # When you try to set state to ongoing on poll and
        # agenda item is not ongoing an exception should be raised.
        self.config.include('voteit.core.testing_helpers.register_workflows')
        self.config.include('voteit.core.testing_helpers.register_catalog')
        #self.config.include('voteit.core.models.meeting')
        #self.config.include('voteit.core.models.agenda_item')
        request = testing.DummyRequest()
        self.config.begin(request)
        root = poll_fixture()
        root['m'].wf_state = 'ongoing'
        obj = root['m']['ai']
        obj.wf_state = 'upcoming'
        self.assertRaises(Exception, obj.set_workflow_state, 'ongoing')
        ai = find_interface(obj, IAgendaItem)
        ai.wf_state = 'ongoing'
        obj.wf_state = 'ongoing'

    def test_ongoing_wo_proposal(self):
        self.config.include('voteit.core.testing_helpers.register_workflows')
        self.config.include('voteit.core.testing_helpers.register_catalog')
        self.config.include('voteit.core.models.poll')
        request = testing.DummyRequest()
        self.config.begin(request)
        root = poll_fixture()
        root['m'].wf_state = 'ongoing'
        ai = root['m']['ai']
        poll = ai['poll']
        ai.wf_state = 'ongoing'
        poll.wf_state = 'upcoming'
        # remove all proposals on poll
        poll.proposals = ()
        self.assertRaises(HTTPForbidden, poll.workflow.do_transition, 'ongoing')

    def test_get_proposal_by_uid(self):
        self.config.include('voteit.core.testing_helpers.register_catalog')
        root = poll_fixture()
        agenda_item = root['m']['ai']
        uid = agenda_item['prop1'].uid
        poll = agenda_item['poll']
        poll.proposal_uids = (uid,)
        prop = poll.get_proposal_by_uid(uid)
        self.assertEqual(prop, agenda_item['prop1'])
        
    def test_get_proposal_by_uid_non_existing_uid(self):
        self.config.include('voteit.core.testing_helpers.register_catalog')
        root = poll_fixture()
        agenda_item = root['m']['ai']
        poll = agenda_item['poll']
        # This will break the reference
        poll.proposals = ()
        uid = agenda_item['prop1'].uid
        self.assertRaises(KeyError, poll.get_proposal_by_uid, uid)


class PollMethodsTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_chameleon')
        self.config.include('voteit.core.testing_helpers.register_catalog')

    def tearDown(self):
        testing.tearDown()

    def test_email_voters_about_ongoing_poll(self):
        root = active_poll_fixture(self.config)
        self.config.testing_securitypolicy('userid', permissive = True)
        poll = root['meeting']['ai']['poll']
        root['meeting'].poll_notification_setting = True
        request = testing.DummyRequest()
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 0)
        security.unrestricted_wf_transition_to(poll, 'ongoing')
        self.assertEqual(len(mailer.outbox), 1)
        self.failUnless('this@that.com' in mailer.outbox[0].recipients)

    def test_ongoing_poll_callback_agenda_item_not_ongoing_error(self):
        request = testing.DummyRequest()
        self.config.begin(request)
        root = active_poll_fixture(self.config)
        ai = root['meeting']['ai']
        ai.wf_state = 'upcoming'
        self.assertRaises(HTTPForbidden, security.unrestricted_wf_transition_to, ai['poll'], 'ongoing')


class PollPermissionTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing')
        self.config.include('voteit.core.testing_helpers.register_catalog')
        self.config.include('voteit.core.testing_helpers.register_workflows')
        request = testing.DummyRequest()
        self.config.begin(request)

    def tearDown(self):
        testing.tearDown()

    @property
    def pap(self):
        policy = ACLAuthorizationPolicy()
        return policy.principals_allowed_by_permission

    def _make_obj(self):
        """ Poll object need to be in the context of an Agenda Item to work properly
        """
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.poll import Poll
        from voteit.core.models.proposal import Proposal
        from voteit.core.models.agenda_item import AgendaItem
        root['ai'] = ai = AgendaItem()
        poll = Poll()
        ai['prop'] = proposal = Proposal()
        poll.set_field_value('proposals', set(proposal.uid))
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
        poll.__parent__.wf_state = 'upcoming'
        poll.wf_state = 'upcoming'
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(poll, security.EDIT), admin | moderator)
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())
        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_upcoming_w_private_ai(self):
        poll = self._make_obj()
        poll.wf_state = 'upcoming'
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator )
        self.assertEqual(self.pap(poll, security.EDIT), admin | moderator)
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())
        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_ongoing(self):
        poll = self._make_obj()
        ai = find_interface(poll, IAgendaItem)
        ai.wf_state = 'ongoing'
        poll.wf_state = 'upcoming'
        poll.wf_state = 'ongoing'
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(poll, security.EDIT), set())
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(poll, security.ADD_VOTE), voter)
        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)
        
    def test_closed(self):
        poll = self._make_obj()
        self._register_majority_poll(poll)
        ai = find_interface(poll, IAgendaItem)
        ai.wf_state = 'ongoing'
        poll.wf_state = 'upcoming'
        poll.wf_state = 'ongoing'
        poll.wf_state = 'closed'
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(poll, security.EDIT), set())
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())
        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), set())

    def test_canceled(self):
        poll = self._make_obj()
        ai = find_interface(poll, IAgendaItem)
        ai.wf_state = 'ongoing'
        poll.wf_state = 'upcoming'
        poll.wf_state = 'ongoing'
        poll.wf_state = 'canceled'
        self._register_majority_poll(poll)
        self.assertEqual(self.pap(poll, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(poll, security.EDIT), set())
        self.assertEqual(self.pap(poll, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(poll, security.ADD_VOTE), set())
        self.assertEqual(self.pap(poll, security.CHANGE_WORKFLOW_STATE), admin | moderator)
