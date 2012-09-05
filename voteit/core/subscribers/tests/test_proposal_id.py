from unittest import TestCase

from pyramid import testing
from repoze.folder.events import ObjectAddedEvent
from zope.component.event import objectEventNotify

from voteit.core.testing_helpers import bootstrap_and_fixture


class ProposalIDSubscriberTests(TestCase):

    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.catalog')
        self.config.scan('voteit.core.subscribers.catalog')

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.subscribers.proposal_id import proposal_id
        return proposal_id
    
    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m1'] = Meeting()
        return root['m1']

    @property
    def _prop(self):
        from voteit.core.models.proposal import Proposal
        return Proposal

    def test_no_creator_assigned(self):
        context = self._fixture()
        context['prop'] = obj = self._prop()
        self.assertRaises(ValueError, self._fut, obj, None)
        
    def test_proposal_id(self):
        context = self._fixture()
        context['o'] = obj = self._prop(creators=('admin',))
        self._fut(obj, None)
        self.assertIn('admin-1', obj.get_field_value('aid'))

    def test_proposal_id_second(self):
        context = self._fixture()
        context['o1'] = obj = self._prop(creators=('admin',))
        self._fut(obj, None)
        context['o2'] = obj = self._prop(creators=('admin',))
        self._fut(obj, None)
        self.assertEqual('admin-2', obj.get_field_value('aid'))

    def test_proposal_id_different_users(self):
        context = self._fixture()
        context['o1'] = obj = self._prop(creators=('admin',))
        self._fut(obj, None)
        context['o2'] = obj = self._prop(creators=('john_doe',))
        self._fut(obj, None)
        context['o3'] = obj = self._prop(creators=('admin',))
        self._fut(obj, None)
        self.assertEqual('admin-2', obj.get_field_value('aid'))

    def test_proposal_id_different_meetings(self):
        context = self._fixture()
        from voteit.core.models.meeting import Meeting
        root = context.__parent__
        root['m2'] = m2 = Meeting()
        m2['p1'] = self._prop(creators=('admin',))
        self._fut(m2['p1'], None)
        m2['p2'] = self._prop(creators=('admin',))
        self._fut(m2['p2'], None)
        context['p1'] = self._prop(creators=('admin',))
        self._fut(context['p1'], None)
        self.assertEqual('admin-1', context['p1'].get_field_value('aid'))

    def test_integration(self):
        context = self._fixture()
        self.config.scan('voteit.core.subscribers.proposal_id')
        context['o1'] = obj = self._prop(creators=('admin',))
        self.assertEqual('admin-1', obj.get_field_value('aid'))

