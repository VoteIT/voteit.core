import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class AtUseridLinkTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import at_userid_link
        return at_userid_link
        
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_function(self):
        from voteit.core.interfaces import IWorkflowStateChange
        value = self._fut('@admin', self._fixture())
        self.assertIn('/m/_userinfo?userid=admin', value)

class GenerateSlugTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import generate_slug
        return generate_slug
        
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_unique(self):
        context = self._fixture()
        value = self._fut(context, u'o1')
        self.assertIn(u'o1', value)
        
    def test_same(self):
        context = self._fixture()
        from voteit.core.models.proposal import Proposal 
        context['o1'] = Proposal()
        value = self._fut(context, u'o1')
        self.assertIn(u'o1-1', value)
        
    def test_cant_find_unique(self):
        context = self._fixture()
        from voteit.core.models.proposal import Proposal
        context[u'o1'] = Proposal()
        for i in range(1, 101):
            context[u'o1-%s' % i] = Proposal()
        self.assertRaises(KeyError, self._fut, context, u'o1')