import unittest

from pyramid import testing
from pyramid.traversal import find_interface
from zope.interface.verify import verifyObject

from voteit.core.app import register_poll_plugin
from voteit.core.models.interfaces import IAgendaItem

    
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
        ai['poll'] = Poll()
        
        return MajorityPollPlugin( ai['poll'] )

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IPollPlugin
        obj = self._make_obj()
        self.assertTrue(verifyObject(IPollPlugin, obj))

    def test_get_vote_schema(self):
        obj = self._make_obj()
        
        #Shouldn't type return a string? :)
        from colander import SchemaNode
        self.assertEqual(type(obj.get_vote_schema()), SchemaNode)
    
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
        self.config = testing.setUp()
        
        #Enable workflows
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')
        
        #Register poll plugin
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        register_poll_plugin(MajorityPollPlugin, verify=0, registry=self.config.registry)

        #Add agenda item - needed for lookups
        from voteit.core.models.agenda_item import AgendaItem
        ai = AgendaItem()

        #Add a poll
        from voteit.core.models.poll import Poll
        ai['poll'] = Poll()
        #Wrap in correct context
        self.poll = ai['poll']
        #Select plugin to use
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
        v1.set_vote_data({'proposal':self.ai['p1'].uid})
        self.poll['v1'] = v1
        
        v2 = vote_cls()
        v2.set_vote_data({'proposal':self.ai['p1'].uid})
        self.poll['v2'] = v2
        
        v3 = vote_cls()
        v3.set_vote_data({'proposal':self.ai['p2'].uid})
        self.poll['v3'] = v3
    
    def _close_poll(self):
        request = testing.DummyRequest()
        
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
        self._add_votes()
        self._close_poll()
        plugin = self.poll.get_poll_plugin()
        request = testing.DummyRequest()
        self.assertTrue('p1' in plugin.render_result(request))
        
