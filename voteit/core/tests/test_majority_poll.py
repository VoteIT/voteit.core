import unittest

from pyramid import testing
from zope.interface.verify import verifyObject

from voteit.core import register_poll_plugin

    
class MPUnitTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _make_obj(self):
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        from voteit.core.models.poll import Poll
        return MajorityPollPlugin( Poll() )

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IPollPlugin
        obj = self._make_obj()
        self.assertTrue(verifyObject(IPollPlugin, obj))


class MPIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        
        #Enable workflows
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')
        
        #Register poll plugin
        from voteit.core.plugins.majority_poll import MajorityPollPlugin
        register_poll_plugin(MajorityPollPlugin, verify=0, registry=self.config.registry)

        #Add a poll
        from voteit.core.models.poll import Poll
        self.poll = Poll()
        #Select plugin to use
        self.poll.set_field_value('poll_plugin', MajorityPollPlugin.name)
        
        #Add proposals
        from voteit.core.models.proposal import Proposal
        p1 = Proposal()
        p1.uid = 'p1uid' #To make it simpler to test against
        self.poll['p1'] = p1
        p2 = Proposal()
        p2.uid = 'p2uid' #To make it simpler to test against
        self.poll['p2'] = p2
        
        #Select proposals for this poll
        self.poll.proposal_uids = (p1.uid, p2.uid, )
        
    def tearDown(self):
        testing.tearDown()

    def test_majority_poll(self):
        plugin = self.poll.get_poll_plugin()
        #Add 3 votes
        v1 = plugin.get_vote_class()()
        v1.set_vote_data(self.poll['p1'].uid)
        self.poll['v1'] = v1
        
        v2 = plugin.get_vote_class()()
        v2.set_vote_data(self.poll['p1'].uid)
        self.poll['v2'] = v2
        
        v3 = plugin.get_vote_class()()
        v3.set_vote_data(self.poll['p2'].uid)
        self.poll['v3'] = v3
        
        request = testing.DummyRequest()
        self.poll.set_workflow_state(request, 'planned')
        self.poll.set_workflow_state(request, 'ongoing')
        self.poll.set_workflow_state(request, 'closed')

        self.assertEqual(2, len(self.poll.poll_result))

        