import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_security_policies
from voteit.core.testing_helpers import register_catalog


class MeetingViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.participants import ParticipantsView
        return ParticipantsView
    
    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        root.users['dummy'] = User()
        return meeting

    def _load_vcs(self):
        self.config.scan('voteit.core.views.components.main')
        self.config.scan('voteit.core.views.components.meeting')

    def test_participants_view(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.participants_view()
        self.assertIn('participants', response)

    def test_participants_json_data(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.participants_json_data()
        expected = {'first_name': u'VoteIT', 'last_name': u'Administrator',
                    'email': '', 'roles': ('role:Admin',)}
        self.assertEqual(response['admin'], expected)
        expected = {'first_name': u"", 'last_name': u"", 'email': u"", 'roles': ()}
        self.assertEqual(response['dummy'], expected)

