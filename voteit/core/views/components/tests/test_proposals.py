import unittest

from pyramid import testing

from voteit.core.testing_helpers import active_poll_fixture


class ProposalsComponentTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.views.components.proposals import proposal_listing
        return proposal_listing

    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        from voteit.core.models.poll import Poll
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        #self.config.scan('voteit.core.models.proposal')
        self.config.scan('voteit.core.views.components.main')
        self.config.scan('voteit.core.views.components.poll')
        self.config.scan('voteit.core.views.components.moderator_actions')
        self.config.scan('voteit.core.views.components.user_tags')
        self.config.scan('voteit.core.views.components.proposals')
        self.config.scan('voteit.core.views.components.metadata_listing')
        self.config.include('voteit.core.testing_helpers.register_catalog')
        root = active_poll_fixture(self.config)
        return root['meeting']['ai']
    
    def _api(self, context=None, request=None):
        from voteit.core.views.api import APIView
        context = context and context or testing.DummyResource()
        request = request and request or testing.DummyRequest()
        request.context = context
        return APIView(context, request)

    def _va(self):
        class ViewAction():
            pass
        return ViewAction()

    def test_proposal_listing_ai_dummy_sec(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        va = self._va()
        api = self._api(context, request)
        response = self._fut(context, request, va, api=api)
        self.assertIn('Proposal 1', response)
