from unittest import TestCase

from pyramid import testing
from repoze.folder.events import ObjectAddedEvent
from zope.component.event import objectEventNotify

from voteit.core.testing_helpers import bootstrap_and_fixture


class MentionSubscriberTests(TestCase):

    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.subscribers.mention import transform_at_links
        return transform_at_links
    
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_proposal(self):
        ai = self._fixture()
        from voteit.core.models.proposal import Proposal 
        ai['o'] = obj = Proposal(title="@admin")
        self._fut(obj, None)
        self.assertIn('/m/_userinfo?userid=admin', obj.title)
        
    def test_discussion_post(self):
        ai = self._fixture()
        from voteit.core.models.discussion_post import DiscussionPost 
        ai['o'] = obj = DiscussionPost(text="@admin")
        self._fut(obj, None)
        self.assertIn('/m/_userinfo?userid=admin', obj.title)