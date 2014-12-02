import unittest

from pyramid import testing
from webob.multidict import MultiDict

from voteit.core.testing_helpers import bootstrap_and_fixture


class AddPollFormTests(unittest.TestCase):
     
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)
 
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.poll import AddPollForm
        return AddPollForm

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        return meeting

    def test_add_poll(self):
        self.config.testing_securitypolicy('dummy', permissive = True)
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.scan('voteit.core.models.poll')
        self.config.scan('voteit.core.schemas.poll')
        self.config.include('voteit.core.plugins.majority_poll')
        self.config.include('voteit.core.models.flash_messages')
        meeting = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        meeting['ai'] = context = AgendaItem()
        request = testing.DummyRequest(params={'content_type': 'Poll'}, post=MultiDict([('add', 'add'), 
                                                                                       ('title', 'Dummy poll'),
                                                                                       ('description', 'description'),
                                                                                       ('poll_plugin', 'majority_poll'),
                                                                                       ('__start__', 'proposals:sequence'),
                                                                                       ('__end__', 'proposals:sequence'),
                                                                                       ('reject_proposal_title', 'Reject all proposals'),
                                                                                       ('start_time', '2012-05-15 12:00'),
                                                                                       ('end_time', '2012-05-16 12:00')]))
        obj = self._cut(context, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location.split('#')[0], 'http://example.com/m/ai/') #A redirect with an anchor
