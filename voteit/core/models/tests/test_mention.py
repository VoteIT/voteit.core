from unittest import TestCase

from pyramid import testing
from pyramid_mailer import get_mailer
from arche.utils import send_email

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import attach_request_method


class MentionFunctionalTests(TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        attach_request_method(self.request, send_email, 'send_email')
        self.config = testing.setUp(request = self.request)
        self.config.include('voteit.core.models.mention')
        self.config.include('pyramid_mailer.testing')

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['users']['admin'].email = 'this@that.com'
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_proposal_added(self):
        ai = self._fixture()
        from voteit.core.models.proposal import Proposal 
        obj = Proposal(text="@admin")
        ai['o'] = obj
        mailer = get_mailer(self.request)
        self.assertEqual(len(mailer.outbox), 1)

    def test_update_only_notifies_once(self):
        ai = self._fixture()
        from voteit.core.models.proposal import Proposal 
        obj = Proposal(text="@admin")
        ai['o'] = obj
        mailer = get_mailer(self.request)
        self.assertEqual(len(mailer.outbox), 1)
        obj.update(text = "@admin @admin")
        self.assertEqual(len(mailer.outbox), 1)

    def test_update_triggers(self):
        ai = self._fixture()
        from voteit.core.models.proposal import Proposal 
        obj = Proposal()
        ai['o'] = obj
        mailer = get_mailer(self.request)
        self.assertEqual(len(mailer.outbox), 0)
        obj.update(text = "@admin")
        self.assertEqual(len(mailer.outbox), 1)

    def test_meeting_can_turn_off_notification(self):
        ai = self._fixture()
        ai.__parent__.set_field_value('mention_notification_setting', False)
        from voteit.core.models.proposal import Proposal 
        ai['o'] = Proposal(text = "@admin")
        mailer = get_mailer(self.request)
        self.assertEqual(len(mailer.outbox), 0)

    def test_dont_die_with_nonexisting_userid(self):
        ai = self._fixture()
        from voteit.core.models.proposal import Proposal 
        ai['o'] = Proposal(text = "@noonehere")
        mailer = get_mailer(self.request)
        self.assertEqual(len(mailer.outbox), 0)
