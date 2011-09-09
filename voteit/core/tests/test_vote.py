import unittest

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from zope.interface.verify import verifyObject
from pyramid.threadlocal import get_current_registry

from voteit.core import security

admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
authenticated = set([Authenticated])
participant = set([security.ROLE_PARTICIPANT])
viewer = set([security.ROLE_VIEWER])
voter = set([security.ROLE_VOTER])
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
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        # load workflow
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.vote import Vote
        return Vote()

    def _make_poll(self):
        from voteit.core.models.poll import Poll
        from voteit.core.models.proposal import Proposal
        from voteit.core.app import register_poll_plugin
        from voteit.core.plugins.majority_poll import MajorityPollPlugin

        registry = get_current_registry()
        register_poll_plugin(MajorityPollPlugin, registry=registry)
        

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
        poll = self._make_poll()
        ai['poll'] = poll
        poll.set_workflow_state(request, 'planned')
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
        ai = self._make_ai()
        poll = self._make_poll()
        ai['poll'] = poll
        poll.set_workflow_state(request, 'planned')
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

