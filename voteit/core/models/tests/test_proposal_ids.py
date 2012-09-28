import unittest

from pyramid import testing
from zope.interface.verify import verifyObject


class ProposalIdsTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_adapted_obj(self):
        from voteit.core.models.proposal_ids import ProposalIds
        from voteit.core.models.meeting import Meeting
        context = Meeting()
        return ProposalIds(context)

    def test_interface(self):
        from voteit.core.models.interfaces import IProposalIds
        obj = self._make_adapted_obj()
        self.assertTrue(verifyObject(IProposalIds, obj))

    def test_add(self):
        obj = self._make_adapted_obj()
        
        obj.add('BennyBoy', 1)
        self.assertIn('BennyBoy', obj._proposal_ids)
        self.assertEqual(obj._proposal_ids['BennyBoy'], 1)
        
        obj.add('BennyBoy', 2)
        self.assertIn('BennyBoy', obj._proposal_ids)
        self.assertEqual(obj._proposal_ids['BennyBoy'], 2)
    
    def test_get(self):
        obj = self._make_adapted_obj()
        
        obj.add('James', 1)
        self.assertEqual(obj.get('James'), 1)

    def test_registration(self):
        self.config.include('voteit.core.models.proposal_ids')
        from voteit.core.models.meeting import Meeting
        context = Meeting()
        from voteit.core.models.interfaces import IProposalIds
        adapter = self.config.registry.queryAdapter(context, IProposalIds)
        self.failUnless(IProposalIds.providedBy(adapter))
