import unittest

from pyramid import testing
from pyramid.exceptions import NotFound

from voteit.core.testing_helpers import bootstrap_and_fixture


class UsersViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai
    
    def _enable_catalog(self):
        self.config.scan('voteit.core.subscribers.catalog')
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.catalog')
    
    def test_proposal_redirect_to_agenda_item(self):
        ai = self._fixture()
        from voteit.core.models.proposal import Proposal
        ai['p'] = context = Proposal()
        request = testing.DummyRequest()
        from voteit.core.views.redirect import proposal_redirect_to_agenda_item
        response = proposal_redirect_to_agenda_item(context, request)
        self.assertEqual(response.location, 'http://example.com/m/ai/#%s' % context.uid)
        
    def test_proposal_redirect_to_agenda_item_not_found(self):
        from voteit.core.models.proposal import Proposal
        context = Proposal()
        request = testing.DummyRequest()
        from voteit.core.views.redirect import proposal_redirect_to_agenda_item
        self.assertRaises(NotFound, proposal_redirect_to_agenda_item, context, request)
        
    def test_discussion_redirect_to_agenda_item(self):
        self._enable_catalog()
        ai = self._fixture()
        from voteit.core.models.discussion_post import DiscussionPost
        ai['d'] = context = DiscussionPost()
        request = testing.DummyRequest()
        from voteit.core.views.redirect import discussion_redirect_to_agenda_item
        response = discussion_redirect_to_agenda_item(context, request)
        self.assertEqual(response.location, 'http://example.com/m/ai/#%s' % context.uid)
        
    def test_discussion_redirect_to_agenda_item_all(self):
        self._enable_catalog()
        ai = self._fixture()
        from voteit.core.models.discussion_post import DiscussionPost
        ai['d1'] = context = DiscussionPost()
        ai['d2'] = DiscussionPost()
        ai['d3'] = DiscussionPost()
        ai['d4'] = DiscussionPost()
        ai['d5'] = DiscussionPost()
        ai['d6'] = DiscussionPost()
        request = testing.DummyRequest()
        from voteit.core.views.redirect import discussion_redirect_to_agenda_item
        response = discussion_redirect_to_agenda_item(context, request)
        self.assertEqual(response.location, 'http://example.com/m/ai/?discussions=all#%s' % context.uid)
        
    def test_discussion_redirect_to_agenda_item_not_found(self):
        self._enable_catalog()
        from voteit.core.models.discussion_post import DiscussionPost
        context = DiscussionPost()
        request = testing.DummyRequest()
        from voteit.core.views.redirect import discussion_redirect_to_agenda_item
        self.assertRaises(NotFound, discussion_redirect_to_agenda_item, context, request)