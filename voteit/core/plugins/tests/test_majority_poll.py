import unittest

from pyramid import testing
from pyramid.request import apply_request_extensions
from pyramid.traversal import find_interface, find_root
from zope.interface.verify import verifyObject
import colander

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.testing_helpers import attach_request_method, bootstrap_and_fixture
from voteit.core.helpers import creators_info
from voteit.core.helpers import get_userinfo_url


class MPUnitTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _make_obj(self):
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        from voteit.core.models.poll import Poll
        from voteit.core.models.agenda_item import AgendaItem
        self.config.include('arche.testing.catalog')
        self.root = bootstrap_and_fixture(self.config)
        self.root['ai'] = ai = AgendaItem()
        ai['poll'] = self.poll = Poll()
        return MajorityPollPlugin( ai['poll'] )

    def test_verify_implementation(self):
        obj = self._make_obj()
        self.assertTrue(verifyObject(IPollPlugin, obj))

    def test_get_vote_schema(self):
        obj = self._make_obj()
        self.assertIsInstance(obj.get_vote_schema(), colander.Schema)
    
    def test_render_raw_data(self):
        """ Test that render_raw_data returns a Response
        """
        obj = self._make_obj()
        obj.context.ballots = "Hello world"
        result = obj.render_raw_data()
        from pyramid.response import Response
        self.assertTrue(isinstance(result, Response))
        self.assertTrue(result.body, "Hello world")


class MPIntegrationTests(unittest.TestCase):
    """ Note that this is a mix of unit and integration tests.
        The plugin as such can't be tested without adding test fixture.
    """
    
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        self.config.testing_securitypolicy(userid='admin')
        self.config.include('arche.testing')
        self.config.include('voteit.core.testing_helpers.register_catalog')
        self.config.include('voteit.core.testing_helpers.register_workflows')
        self.config.include('voteit.core.models.poll')
        self.config.include('voteit.core.helpers')
        #Register poll plugin
        self.config.include('voteit.core.plugins.majority_poll')
        #Add root
        from voteit.core.models.site import SiteRoot
        self.root = root = SiteRoot()
        #Add users
        from voteit.core.models.users import Users
        root['users'] = users = Users()
        from voteit.core.models.user import User
        users['admin'] = User()
        #Add meeting
        from voteit.core.models.meeting import Meeting
        root['m'] = self.meeting = m = Meeting()
        #Add agenda item - needed for lookups
        from voteit.core.models.agenda_item import AgendaItem
        m['ai'] = ai = AgendaItem()
        #Add a poll
        from voteit.core.models.poll import Poll
        ai['poll'] = Poll()
        #Wrap in correct context
        self.poll = ai['poll']
        #Select plugin to use
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        self.poll.poll_plugin = MajorityPollPlugin.name
        #Add proposals
        from voteit.core.models.proposal import Proposal
        ai['p1'] = p1 = Proposal(text = 'p1', creators = ['admin'], aid = 'one', uid='p1uid')
        ai['p2'] = p2 = Proposal(text = 'p2', creators = ['admin'], aid = 'two', uid='p2uid')
        #Select proposals for this poll
        self.poll.proposals = (p1.uid, p2.uid, )
        self.ai = ai
        
    def tearDown(self):
        testing.tearDown()
    
    def _add_votes(self):
        plugin = self.poll.get_poll_plugin()
        vote_cls = plugin.get_vote_class()
        v1 = vote_cls()
        self.poll['v1'] = v1
        v1.set_vote_data({'proposal':self.ai['p1'].uid})
        v2 = vote_cls()
        self.poll['v2'] = v2
        v2.set_vote_data({'proposal':self.ai['p1'].uid})
        v3 = vote_cls()
        self.poll['v3'] = v3
        v3.set_vote_data({'proposal':self.ai['p2'].uid})
    
    def _close_poll(self):
        request = self.request
        m = find_interface(self.poll, IMeeting)
        m.wf_state = 'ongoing'
        ai = find_interface(self.poll, IAgendaItem)
        ai.wf_state = 'ongoing'
        self.poll.wf_state = 'upcoming'
        self.poll.wf_state = 'ongoing'
        self.poll.wf_state = 'closed'

    def test_poll_result_created(self):
        self._add_votes()
        self._close_poll()
        self.assertEqual(2, len(self.poll.poll_result))

    def test_render_raw_data(self):
        self._add_votes()
        self._close_poll()
        plugin = self.poll.get_poll_plugin()
        self.assertEqual(plugin.render_raw_data().body,
                         "(({'proposal': 'p1uid'}, 2), ({'proposal': 'p2uid'}, 1))")

    def test_render_result(self):
        self.config.include('pyramid_chameleon')
        apply_request_extensions(self.request)
        self.request.root = self.root
        self.request.meeting = self.meeting
        from voteit.core.views.poll import PollResultsView
        self._add_votes()
        self._close_poll()
        plugin = self.poll.get_poll_plugin()
        request = self.request
        request.context = self.poll
        view = PollResultsView(self.poll, request)
        response = view()
        self.assertEqual(response.status, '200 OK')
        self.assertIn('#one', response.body)
