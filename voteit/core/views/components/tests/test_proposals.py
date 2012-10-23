import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class ProposalsComponentTests(unittest.TestCase):
    
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
        meeting['ai'] = ai = AgendaItem()
        ai['p1'] = Proposal(title='Proposal 1')
        ai['p2'] = Proposal(title='Proposal 2')
        ai['p3'] = Proposal(title='Proposal 3', creators= ['dummy'])
        ai['p4'] = Proposal(title='Proposal 4')
        ai['p4'].set_workflow_state(testing.DummyRequest(), 'voting')
        return ai
    
    def _api(self, context=None, request=None):
        from voteit.core.views.api import APIView
        context = context and context or testing.DummyResource()
        request = request and request or testing.DummyRequest()
        return APIView(context, request)

    def _va(self):
        class ViewAction():
            pass
        return ViewAction()
    
    def _enable_catalog(self):
        self.config.scan('voteit.core.subscribers.catalog')
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.catalog')
        
    def test_proposal_listing(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.scan('voteit.core.views.components.main')
        self.config.scan('voteit.core.views.components.moderator_actions')
        self.config.scan('voteit.core.views.components.creators_info')
        self.config.scan('voteit.core.views.components.user_tags')
        self.config.scan('voteit.core.views.components.proposals')
        self.config.scan('voteit.core.views.components.meta_data_listing')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._enable_catalog()
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        from voteit.core.views.components.proposals import proposal_listing
        response = proposal_listing(context, request, va, api=api)
        self.assertIn('Proposal 1', response)
