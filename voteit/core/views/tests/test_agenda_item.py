import datetime
import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture



class AgendaItemViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.agenda_item import AgendaItemView
        return AgendaItemView
    
    def _fixture(self):
        """ Normal context for this view is an agenda item. """
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        
        return ai
    
    def test_agenda_item_view(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        
        self.config.scan('voteit.core.views.components.main')
        self.config.scan('voteit.core.views.components.agenda_item')
        self.config.scan('voteit.core.views.components.proposals')
        self.config.scan('voteit.core.views.components.discussions')
        
        context = self._fixture()
        request = testing.DummyRequest()
         
        aiv = self._cut(context, request)
        response = aiv.agenda_item_view()
        #FIXME: actually check for something in the response
        self.assertIsNotNone(response)
        
    def test_inline_add_form_proposal(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        
        self.config.scan('voteit.core.models.proposal')
        self.config.scan('voteit.core.schemas.proposal')
        
        context = self._fixture()
        request = testing.DummyRequest(params={'content_type': 'Proposal'})
         
        aiv = self._cut(context, request)
        response = aiv.inline_add_form()

        self.assertIn(u"content_type=Proposal", response.ubody)
        
    def test_inline_add_form_discussion_post(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        
        self.config.scan('voteit.core.models.discussion_post')
        self.config.scan('voteit.core.schemas.discussion_post')
        
        context = self._fixture()
        request = testing.DummyRequest(params={'content_type': 'DiscussionPost'})
         
        aiv = self._cut(context, request)
        response = aiv.inline_add_form()

        self.assertIn(u"content_type=DiscussionPost", response.ubody)
        
    def test_discussion_more(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        
        from voteit.core.models.discussion_post import DiscussionPost
        context = DiscussionPost() 
        context.title = "Testing read more view"
        
        request = testing.DummyRequest()
        aiv = self._cut(context, request)
        response = aiv.discussion_more()
        
        self.assertEqual(response['body'], context.title)