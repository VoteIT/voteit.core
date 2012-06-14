import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class AgendaItemViewComponentTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        root = bootstrap_and_fixture(self.config)
        root['m'] = Meeting()
        root['m']['ai'] = AgendaItem()
        return root['m']['ai']

    def _api(self, context=None):
        from voteit.core.views.api import APIView
        context = context and context or testing.DummyResource()
        request = testing.DummyRequest()
        return APIView(context, request)

    def test_proposals(self):
        from voteit.core.views.components.agenda_item import proposals
        self.config.scan('voteit.core.views.components.proposals')
        ai = self._fixture()
        api = self._api(ai)
        self.assertIn('proposals', proposals(ai, api.request, None, api = api))

    def test_discussions(self):
        from voteit.core.views.components.agenda_item import discussions
        self.config.scan('voteit.core.views.components.discussions')
        ai = self._fixture()
        api = self._api(ai)
        self.assertIn('discussions', discussions(ai, api.request, None, api = api))
