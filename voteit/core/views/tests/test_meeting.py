import unittest

from pyramid import testing
from pyramid.request import apply_request_extensions
from voteit.core.security import unrestricted_wf_transition_to

from voteit.core.testing_helpers import bootstrap_and_fixture


class CopyAITests(unittest.TestCase):

    def setUp(self):

        self.config = testing.setUp()
        self.config.include('arche.testing')

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.meeting import copy_ai
        return copy_ai

    def _fixture(self):
        from arche.resources import Document
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.proposal import Proposal
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m'] = m = Meeting()
        m['ai'] = ai = AgendaItem(title='ai')
        ai['p'] = Proposal(text='Some animlas are more equal than others')
        ai['p']['d'] = Document()
        ai['p2'] = Proposal(text='Me wont be there')
        root['m2'] = Meeting()
        request = testing.DummyRequest()
        request.root = root
        apply_request_extensions(request)
        self.config.begin(request)
        ai['p2'].wf_state = 'retracted'
        return root, request

    def test_contained_not_copied(self):
        root, request = self._fixture()
        m2 = root['m2']
        self._fut(m2, root['m']['ai'], copy_types=('Proposal',), only_copy_prop_states=('published',))
        self.assertIn('p', m2['ai'])
        self.assertNotIn('p2', m2['ai'])
        self.assertNotIn('p2', m2['ai'])
        self.assertNotIn('d', m2['ai']['p'])

    def test_parent_is_not_a_copy(self):
        root, request = self._fixture()
        m2 = root['m2']
        self._fut(m2, root['m']['ai'], copy_types=('Proposal',), only_copy_prop_states=('published',))
        self.assertEqual(root['m2']['ai'], root['m2']['ai']['p'].__parent__)
        self.assertEqual(id(root['m2']['ai']), id(root['m2']['ai']['p'].__parent__))

    def test_workflow_reset(self):
        root, request = self._fixture()
        m2 = root['m2']
        self._fut(m2, root['m']['ai'], copy_types=('Proposal',), only_copy_prop_states=('retracted',), reset_wf=True)
        self.assertIn('p2', m2['ai'])
        self.assertNotIn('p', m2['ai'])
        self.assertEqual(m2['ai']['p2'].get_workflow_state(), 'published')
