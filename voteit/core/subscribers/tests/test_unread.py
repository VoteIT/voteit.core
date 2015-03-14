# from unittest import TestCase
# 
# from pyramid import testing
# 
# from voteit.core.testing_helpers import bootstrap_and_fixture
# from voteit.core.models.interfaces import IUnread
# from voteit.core.security import unrestricted_wf_transition_to
# 
# 
# class UnreadSubscriberTests(TestCase):
# 
#     def setUp(self):
#         self.config = testing.setUp()
# 
#     def tearDown(self):
#         testing.tearDown()
# 
#     def _fixture(self):
#         from voteit.core.models.proposal import Proposal
#         self.config.include('voteit.core.testing_helpers.register_catalog')
#         self.config.include('voteit.core.testing_helpers.register_security_policies')
#         root = bootstrap_and_fixture(self.config)
#         root['p'] = Proposal()
#         return root['p']
# 
#     def test_integration(self):
#         self.config.scan('voteit.core.subscribers.unread')
#         prop = self._fixture()
#         unread = self.config.registry.getAdapter(prop, IUnread)
#         self.assertEqual(unread.get_unread_userids(), frozenset([u'admin']))
#         unrestricted_wf_transition_to(prop, u'retracted')
#         self.assertEqual(unread.get_unread_userids(), frozenset())
