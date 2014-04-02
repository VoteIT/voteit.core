import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class InlineAddFormComponentTests(unittest.TestCase):
        
    def setUp(self):
        self.config = testing.setUp()
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)

    def tearDown(self):
        testing.tearDown()
        
    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root.users['some_user'] = User() 
        root['m'] = Meeting()
        root['m']['ai'] = AgendaItem()
        return root['m']['ai']

    def _api(self, context=None):
        from voteit.core.views.api import APIView
        context = context and context or testing.DummyResource()
        request = testing.DummyRequest()
        return APIView(context, request)
    
    def test_inline_add_form_proposals(self):
        from voteit.core.views.components.inline_add_form import inline_add_proposal_form
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        self.config.scan('voteit.core.models.proposal')
        self.config.scan('voteit.core.schemas.proposal')
        ai = self._fixture()
        api = self._api(ai)
        res = inline_add_proposal_form(ai, api.request, None, api = api)
        self.assertIn('inline_add_form', res)
        
    def test_inline_add_form_discussion_post(self):
        from voteit.core.views.components.inline_add_form import inline_add_discussion_form
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        self.config.scan('voteit.core.models.discussion_post')
        self.config.scan('voteit.core.schemas.discussion_post')
        ai = self._fixture()
        api = self._api(ai)
        res = inline_add_discussion_form(ai, api.request, None, api = api)
        self.assertIn('inline_add_form', res)
