import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class SidebarComponentTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai1'] = AgendaItem()
        meeting['ai2'] = AgendaItem()
        meeting['ai3'] = AgendaItem()
        meeting['ai4'] = AgendaItem()
        return meeting
    
    def _api(self, context=None, request=None):
        from voteit.core.views.api import APIView
        context = context and context or testing.DummyResource()
        request = request and request or testing.DummyRequest()
        return APIView(context, request)

    def _va(self, name=None, title=None, kwargs={}):
        class ViewAction():
            def __init__(self, name, title, kwargs):
                self.name = name
                self.title = title
                self.kwargs = kwargs
        return ViewAction(name, title, kwargs)
    
    def _enable_catalog(self):
        self.config.scan('voteit.core.subscribers.catalog')
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.catalog')

    def test_login_box(self):
        self.config.scan('voteit.core.schemas.user')
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.sidebars import login_box
        response = login_box(context, request, va, api=api)
        self.assertIn('<span>Login</span>', response)
