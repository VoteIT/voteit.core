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
    
    def _va(self, ctype):
        class ViewAction():
            def __init__(self, ctype):
                self.kwargs = {'ctype': ctype, }
        return ViewAction(ctype)
    
    def test_inline_add_form_proposals(self):
        from voteit.core.views.components.inline_add_form import inline_add_form
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        ai = self._fixture()
        api = self._api(ai)
        va = self._va('Proposal')
        res = inline_add_form(ai, api.request, va, api = api)
        self.assertIn('inline_add_form', res)
        
    def test_inline_add_form_discussion_post(self):
        from voteit.core.views.components.inline_add_form import inline_add_form
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        ai = self._fixture()
        api = self._api(ai)
        va = self._va('DiscussionPost')
        res = inline_add_form(ai, api.request, va, api = api)
        self.assertIn('inline_add_form', res)