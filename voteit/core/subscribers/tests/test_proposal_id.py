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

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.subscribers.proposal_id import proposal_id
        return proposal_id
    
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m1'] = m1 = Meeting()
        root['m2'] = m2 = Meeting()
        return m1

    def test_proposal_id(self):
        context = self._fixture()
        from voteit.core.models.proposal import Proposal 
        context['o'] = obj = Proposal(creators=('admin',))
        self._fut(obj, None)
        self.assertIn('admin-1', obj.get_field_value('aid'))
        
    def test_proposal_id_second(self):
        context = self._fixture()
        from voteit.core.models.proposal import Proposal 
        context['o1'] = obj = Proposal(creators=('admin',))
        self._fut(obj, None)
        context['o2'] = obj = Proposal(creators=('admin',))
        self._fut(obj, None)
        self.assertIn('admin-2', obj.get_field_value('aid'))
    
    def test_proposal_id_many(self):
        context = self._fixture()
        from voteit.core.models.proposal import Proposal
        for n in range(1, 500): 
            context['o%s'%n] = obj = Proposal(creators=('admin',))
            self._fut(obj, None)
        context['o500'] = obj = Proposal(creators=('admin',))
        self.assertRaises(KeyError, self._fut, obj, None)
        
    def test_proposal_id_different_meetings(self):
        context = self._fixture()
        from voteit.core.models.proposal import Proposal 
        context['o'] = obj = Proposal(creators=('admin',))
        self._fut(obj, None)
        self.assertIn('admin-1', obj.get_field_value('aid'))
        
        context = context.__parent__['m2']
        context['o'] = obj = Proposal(creators=('admin',))
        self._fut(obj, None)
        self.assertIn('admin-1', obj.get_field_value('aid'))