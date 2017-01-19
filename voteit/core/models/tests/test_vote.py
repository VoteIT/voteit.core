import unittest

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from zope.interface.verify import verifyObject

from voteit.core import security


owner = set([security.ROLE_OWNER])


class VoteTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.vote import Vote
        return Vote()
    
    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IVote
        obj = self._make_obj()
        self.assertTrue(verifyObject(IVote, obj))


class VotePermissionTests(unittest.TestCase):
    """ Check permissions for votes. Note that add permission is handled by Poll context. """

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing')
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        self.config.include('voteit.core.testing_helpers.register_workflows')
        self.config.include('voteit.core.models.vote')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.vote import Vote
        return Vote()

    def _make_poll(self):
        from voteit.core.models.poll import Poll
        from voteit.core.models.proposal import Proposal
        self.config.include('voteit.core.plugins.majority_poll')
        poll = Poll()
        poll.set_field_value('poll_plugin', u'majority_poll')
        proposal = Proposal()
        poll.set_field_value('proposals', set(proposal.uid))
        return poll

    def _make_ai(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()

    def test_ongoing_poll_context(self):
        request = testing.DummyRequest()
        ai = self._make_ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        poll = self._make_poll()
        ai['poll'] = poll
        poll.set_workflow_state(request, 'upcoming')
        poll.set_workflow_state(request, 'ongoing')
        obj = self._make_obj()
        poll['vote'] = obj
        #View
        self.assertEqual(self.pap(obj, security.VIEW), owner)
        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), owner)
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), owner)

    def test_closed_poll_context(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(registry=self.config.registry, request=request)
        ai = self._make_ai()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        poll = self._make_poll()
        ai['poll'] = poll
        poll.set_workflow_state(request, 'upcoming')
        poll.set_workflow_state(request, 'ongoing')
        poll.set_workflow_state(request, 'closed')
        obj = self._make_obj()
        poll['vote'] = obj
        #View
        self.assertEqual(self.pap(obj, security.VIEW), owner)
        #Edit
        self.assertEqual(self.pap(obj, security.EDIT), set())
        #Delete
        self.assertEqual(self.pap(obj, security.DELETE), set())
