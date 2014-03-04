from unittest import TestCase

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.interface.verify import verifyClass

from voteit.core.models.interfaces import IProposalIds


class UserIDBasedPropsalIdsTests(TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.proposal_ids import UserIDBasedPropsalIds
        return UserIDBasedPropsalIds

    @property
    def _meeting(self):
        from voteit.core.models.meeting import Meeting
        return Meeting

    @property
    def _prop(self):
        from voteit.core.models.proposal import Proposal
        return Proposal

    def test_verify_obj(self):
        obj = self._cut(self._meeting())
        self.assertTrue(verifyObject(IProposalIds, obj))

    def test_verify_class(self):
        self.assertTrue(verifyClass(IProposalIds, self._cut))

    def test_add(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        meeting = self._meeting()
        meeting['ai'] = ai = AgendaItem()
        obj = self._cut(meeting)
        ai['p1'] = Proposal(creators = ['BennyBoy'])
        obj.add(ai['p1'])
        self.assertIn('BennyBoy', obj.proposal_ids)
        self.assertEqual(obj.proposal_ids['BennyBoy'], 1)
        ai['p2'] = Proposal(creators = ['BennyBoy'])
        obj.add(ai['p2'])
        self.assertEqual(obj.proposal_ids['BennyBoy'], 2)

    def test_add_also_adds_to_proposal(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        meeting = self._meeting()
        meeting['ai'] = ai = AgendaItem()
        obj = self._cut(meeting)
        ai['p1'] = prop = Proposal(creators = ['BennyBoy'])
        obj.add(prop)
        self.assertIn('aid', prop.field_storage)
        self.assertIn('aid_int', prop.field_storage)
        self.assertEqual(prop.get_field_value('aid'), u"BennyBoy-1")
        self.assertEqual(prop.get_field_value('aid_int'), 1)

    def test_add_no_creator_assigned(self):
        meeting = self._meeting()
        meeting['prop'] = self._prop()
        obj = self._cut(meeting)
        self.assertRaises(ValueError, obj.add, meeting['prop'])

    def test_integration_with_subscriber_add_different_meetings(self):
        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        self.config.include('voteit.core.models.proposal_ids')
        root['m1'] = m1 = self._meeting()
        root['m2'] = m2 = self._meeting()
        m1['p1'] = self._prop(creators = ['jane'])
        m2['p1'] = self._prop(creators = ['jane'])
        m1['p2'] = self._prop(creators = ['jane'])
        obj1 = self._cut(m1)
        self.assertEqual(obj1.proposal_ids['jane'], 2)
        self.assertEqual(m1['p2'].get_field_value('aid'), u"jane-2")
        obj2 = self._cut(m2)
        self.assertEqual(obj2.proposal_ids['jane'], 1)

    def test_integration(self):
        self.config.include('voteit.core.models.proposal_ids')
        meeting = self._meeting()
        adapter = self.config.registry.queryAdapter(meeting, IProposalIds)
        self.failUnless(IProposalIds.providedBy(adapter))

