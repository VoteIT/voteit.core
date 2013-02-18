import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


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

    def test_participants_view(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.participants_view()
        #FIXME: This test is pointless, we need to at least render the template
        #self.assertIn('participants', response)

    def test_participants_json_data(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self.config.scan('voteit.core.views.components.creators_info')
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.participants_json_data()
        expected = {'userinfo': u'<span class="creators"><a href="http://example.com/m/_userinfo?userid=admin" class="inlineinfo"> VoteIT Administrator (admin)</a></span>',
                    'email': '', 'roles': ('role:Admin',)}
        self.assertEqual(response['admin'], expected)
        expected = {'userinfo': u'<span class="creators"><a href="http://example.com/m/_userinfo?userid=dummy" class="inlineinfo">  (dummy)</a></span>',
                    'email': u"", 'roles': ()}
        self.assertEqual(response['dummy'], expected)

