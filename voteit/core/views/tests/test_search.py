import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class SearchViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()
        self.config.scan('voteit.core.schemas.search')
        #self.config.scan('voteit.core.views.search')

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.search import SearchView
        return SearchView

    def _fixture(self):
        """ Normal context for this view is a meeting. """
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m'] = Meeting()
        return root['m']

    def _enable_catalog(self):
        self.config.scan('voteit.core.subscribers.catalog')
        #self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.catalog')

    def test_normal_render_without_query(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        view_cls = self._cut(context, request)
        self.assertTrue(isinstance(view_cls.search(), dict))

    def test_query_result(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        self._enable_catalog()

        from voteit.core.models.agenda_item import AgendaItem
        context['ai'] = AgendaItem(title = 'Hello world')
        
        request = testing.DummyRequest({'query': 'Hello world', 'search': 'search'})
        view_cls = self._cut(context, request)
        res = view_cls.search()
        
        self.assertEqual(res['results_count'], 1)
