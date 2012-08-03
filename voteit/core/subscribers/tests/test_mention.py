from unittest import TestCase

from pyramid import testing
from pyramid_mailer import get_mailer
from repoze.folder.events import ObjectAddedEvent
from zope.component.event import objectEventNotify

from voteit.core.testing_helpers import bootstrap_and_fixture


class MentionSubscriberTests(TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request = self.request)

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.subscribers.mention import notify
        return notify
    
    def _fixture(self):
        self.config.include('pyramid_mailer.testing')
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['users']['admin'].set_field_value('email', 'this@that.com')
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_proposal(self):
        ai = self._fixture()
        from voteit.core.models.proposal import Proposal 
        ai['o'] = obj = Proposal(title="@admin")
        self._fut(obj, None)
        mailer = get_mailer(self.request)
        self.assertEqual(len(mailer.outbox), 1)
        
    def test_discussion_post(self):
        ai = self._fixture()
        from voteit.core.models.discussion_post import DiscussionPost 
        ai['o'] = obj = DiscussionPost(text="@admin")
        self._fut(obj, None)
        mailer = get_mailer(self.request)
        self.assertEqual(len(mailer.outbox), 1)