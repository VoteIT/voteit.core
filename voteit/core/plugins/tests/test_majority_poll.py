import unittest

from pyramid import testing
from pyramid.traversal import find_interface
from zope.interface.verify import verifyObject

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting

    
class MPUnitTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _make_obj(self):
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        from voteit.core.models.poll import Poll
        from voteit.core.models.agenda_item import AgendaItem

        ai = AgendaItem()
        ai['poll'] = self.poll = Poll()
        
        return MajorityPollPlugin( ai['poll'] )

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IPollPlugin
        obj = self._make_obj()
        self.assertTrue(verifyObject(IPollPlugin, obj))

    def test_get_vote_schema(self):
        #Enable workflows
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')
        
        obj = self._make_obj()
        
        request = testing.DummyRequest()
        from voteit.core.views.api import APIView
        api = APIView(self.poll, request)
        
        #Shouldn't type return a string? :)
        from colander import SchemaNode
        self.assertEqual(type(obj.get_vote_schema(request, api)), SchemaNode)
    
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
        
        #Enable workflows
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')
        
        #Register poll plugin
        self.config.include('voteit.core.plugins.majority_poll')
        
        # Adding catalog
        self.config.include('voteit.core.models.catalog')
        self.config.include('voteit.core.models.unread')
        self.config.include('voteit.core.models.user_tags')
        self.config.scan('voteit.core.subscribers.catalog')
        
        #Add root
        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        #Add users
        from voteit.core.models.users import Users
        root['users'] = users = Users()
        from voteit.core.models.user import User
        users['admin'] = User()
        
        #Add meeting
        from voteit.core.models.meeting import Meeting
        root['m'] = m = Meeting()

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
        self.poll.set_field_value('poll_plugin', MajorityPollPlugin.name)
        
        #Add proposals
        from voteit.core.models.proposal import Proposal
        p1 = Proposal()
        p1.title = 'p1'
        p1.uid = 'p1uid' #To make it simpler to test against
        ai['p1'] = p1
        p2 = Proposal()
        p2.title = 'p2'
        p2.uid = 'p2uid' #To make it simpler to test against
        ai['p2'] = p2
        
        #Select proposals for this poll
        self.poll.proposal_uids = (p1.uid, p2.uid, )
        
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
        m.set_workflow_state(request, 'ongoing')
        
        ai = find_interface(self.poll, IAgendaItem)
        ai.set_workflow_state(request, 'upcoming')
        ai.set_workflow_state(request, 'ongoing')
        
        self.poll.set_workflow_state(request, 'upcoming')
        self.poll.set_workflow_state(request, 'ongoing')
        self.poll.set_workflow_state(request, 'closed')

    def test_poll_result_created(self):
    
        self._add_votes()
        self._close_poll()

        self.assertEqual(2, len(self.poll.poll_result))

    def test_render_raw_data(self):
        self._add_votes()
        self._close_poll()
        plugin = self.poll.get_poll_plugin()
        self.assertEqual(plugin.render_raw_data().body, "(({'proposal': u'p1uid'}, 2), ({'proposal': u'p2uid'}, 1))")
            
    def test_render_result(self):
        self.config.scan('voteit.core.models.proposal')
        self.config.scan('voteit.core.views.components.main')
        self.config.scan('voteit.core.views.components.moderator_actions')
        self.config.scan('voteit.core.views.components.creators_info')
        self.config.scan('voteit.core.views.components.proposals')
        self.config.scan('voteit.core.views.components.user_tags')
        self.config.scan('voteit.core.views.components.meta_data_listing')
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.include('voteit.core.models.date_time_util')
        
        self._add_votes()
        self._close_poll()
        plugin = self.poll.get_poll_plugin()
        request = self.request
        ai = find_interface(self.poll, IAgendaItem)
        request.context = ai
        from voteit.core.views.api import APIView
        api = APIView(ai, request)
        self.assertTrue('p2uid' in plugin.render_result(request, api))
