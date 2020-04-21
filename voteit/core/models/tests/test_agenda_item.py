import unittest
from datetime import datetime

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from voteit.core.testing_helpers import bootstrap_and_fixture
from zope.interface.verify import verifyObject

from voteit.core import security


admin = set([security.ROLE_ADMIN])
moderator = set([security.ROLE_MODERATOR])
authenticated = set([Authenticated])
discuss = set([security.ROLE_DISCUSS])
propose = set([security.ROLE_PROPOSE])
viewer = set([security.ROLE_VIEWER])
voter = set([security.ROLE_VOTER])
owner = set([security.ROLE_OWNER])


class AgendaItemTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing.catalog')
        self.root = bootstrap_and_fixture(self.config)
        self.config.include('voteit.core.testing_helpers.register_workflows')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        from voteit.core.models.poll import Poll
        self.config.include("voteit.core.testing_helpers.register_testing_poll")
        self.root['m'] = m = Meeting()
        m['ai'] = ai = self._cut()
        ai['prop'] = prop = Proposal()
        ai['poll'] = Poll(proposals=[prop.uid])
        ai['poll'].poll_plugin_name = "testing"
        return ai

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IAgendaItem
        obj = self._cut()
        self.assertTrue(verifyObject(IAgendaItem, obj))

    def test_workflow_closed_state_ongoing_poll_exception(self):
        """ When you try to close an agenda items that has an ongoing
            poll in it, it should raise an exception.
        """
        request = testing.DummyRequest()
        self.config.begin(request)
        obj = self._fixture()
        meeting = obj.__parent__
        meeting.set_workflow_state(request, 'ongoing')
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        poll = obj['poll']
        poll.set_workflow_state(request, 'upcoming')
        poll.set_workflow_state(request, 'ongoing')
        self.assertRaises(Exception, obj.set_workflow_state, 'closed')

    def test_timestamp_added_on_close(self):
        self.config.include('voteit.core.subscribers.timestamps') #To add subscriber
        request = testing.DummyRequest()
        self.root['ai'] = ai = self._cut()
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        self.assertFalse(isinstance(ai.end_time, datetime))
        ai.set_workflow_state(request, 'closed')
        self.assertTrue(isinstance(ai.end_time, datetime))

    def test_workflow_state_to_ongoing(self):
        """ When you try to set state to ongoing on agenda item and 
            meeting is not ongoing an exception should be raised.
        """
        request = testing.DummyRequest()
        ai = self._fixture()
        ai.set_workflow_state(request, 'upcoming')
        self.assertRaises(Exception, ai.set_workflow_state, 'ongoing')
        ai.__parent__.set_workflow_state(request, 'ongoing')
        ai.set_workflow_state(request, 'ongoing')


class AgendaItemPermissionTests(unittest.TestCase):
    """ Check permissions in different agenda item states. """

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing')
        self.config.include('voteit.core.models.meeting')
        self.config.include('voteit.core.models.agenda_item')
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission
        self.config.include('voteit.core.testing_helpers.register_workflows')

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem()
    
    def _make_meeting(self):
        from voteit.core.models.meeting import Meeting
        return Meeting()

    def test_private(self):
        obj = self._make_obj()
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator)
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator)
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator)
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), admin | moderator)
        self.assertEqual(self.pap(obj, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_ongoing_with_ongoing_meeting(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'upcoming')
        meeting.set_workflow_state(request, 'ongoing')
        meeting['ai'] = obj
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer )
        self.assertEqual(self.pap(obj, security.EDIT), admin | moderator )
        self.assertEqual(self.pap(obj, security.DELETE), admin | moderator)
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), admin | moderator | propose)
        self.assertEqual(self.pap(obj, security.ADD_POLL), admin | moderator)
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), admin | moderator | discuss)
        self.assertEqual(self.pap(obj, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_closed_ai_in_closed_meeting(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        obj.set_workflow_state(request, 'closed')
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'upcoming')
        meeting.set_workflow_state(request, 'ongoing')
        meeting.set_workflow_state(request, 'closed')
        meeting['ai'] = obj
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer)
        self.assertEqual(self.pap(obj, security.EDIT), set())
        self.assertEqual(self.pap(obj, security.DELETE), set())
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), set())
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), set())
        self.assertEqual(self.pap(obj, security.CHANGE_WORKFLOW_STATE), set())

    def test_closed_ai_in_open_meeting(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        obj.set_workflow_state(request, 'closed')
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'upcoming')
        meeting.set_workflow_state(request, 'ongoing')
        meeting['ai'] = obj
        self.assertEqual(self.pap(obj, security.VIEW), admin | moderator | viewer)
        self.assertEqual(self.pap(obj, security.EDIT), set())
        self.assertEqual(self.pap(obj, security.DELETE), set())
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL), set())
        self.assertEqual(self.pap(obj, security.ADD_POLL), set())
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST), admin | moderator | discuss)
        self.assertEqual(self.pap(obj, security.CHANGE_WORKFLOW_STATE), admin | moderator)

    def test_proposal_block(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'upcoming')
        meeting.set_workflow_state(request, 'ongoing')
        meeting['ai'] = obj
        #Set block
        obj.set_field_value('proposal_block', True)
        #Add proposal
        self.assertEqual(self.pap(obj, security.ADD_PROPOSAL),
                         set([security.ROLE_ADMIN, security.ROLE_MODERATOR]))

    def test_discussion_block(self):
        request = testing.DummyRequest()
        obj = self._make_obj()
        obj.set_workflow_state(request, 'upcoming')
        obj.set_workflow_state(request, 'ongoing')
        meeting = self._make_meeting()
        meeting.set_workflow_state(request, 'upcoming')
        meeting.set_workflow_state(request, 'ongoing')
        meeting['ai'] = obj
        #Set block
        obj.set_field_value('discussion_block', True)
        #Add discussion post
        self.assertEqual(self.pap(obj, security.ADD_DISCUSSION_POST),
                         set([security.ROLE_ADMIN, security.ROLE_MODERATOR]))
