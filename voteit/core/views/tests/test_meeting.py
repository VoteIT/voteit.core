import unittest

from pyramid import testing
from pyramid_mailer import get_mailer

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_catalog


class MeetingViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.meeting import MeetingView
        return MeetingView

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        root.users['dummy'] = User()
        return meeting

    def _load_vcs(self):
        self.config.scan('voteit.core.views.components.main')
        
    def test_meeting_view(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.meeting_view()
        #FIXME: Create a proper test with a rendered template

    def test_meeting_view_no_permission(self):
        ''' View should redirect to request access view '''
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.meeting_view()
        self.assertEqual(response.location, 'http://example.com/m/request_access')
        
    def test_meeting_view_no_permission_not_loggedin(self):
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(permissive=False)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.meeting_view()
        self.assertEqual(response.location, 'http://example.com/m/request_access')
        
    def test_participants_emails(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.participants_emails()
        self.assertIn('participants', response)

    def test_manage_layout(self):
        self.config.scan('voteit.core.schemas.layout')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.manage_layout()
        self.assertIn('form', response)
        
    def test_manage_layout_cancel(self):
        self.config.scan('voteit.core.schemas.layout')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.manage_layout()
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_manage_layout_save(self):
        self.config.scan('voteit.core.schemas.layout')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()

        request = testing.DummyRequest(post = {'save': 'save', 
                                               'meeting_left_widget': '', 
                                               'meeting_right_widget': '', 
                                               'ai_left_widget': '',
                                               'ai_right_widget': '',
                                               'truncate_discussion_length': ''})
        obj = self._cut(context, request)
        response = obj.manage_layout()
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_manage_layout_validation_error(self):
        self.config.scan('voteit.core.schemas.layout')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()

        request = testing.DummyRequest(post = {'save': 'save', 
                                               'meeting_left_widget': '', 
                                               'meeting_right_widget': '', 
                                               'ai_left_widget': '',
                                               'ai_right_widget': '',
                                               'truncate_discussion_length': 'not_integer'})
        obj = self._cut(context, request)
        response = obj.manage_layout()
        self.assertIn('form', response)
        
    def test_request_meeting_access_invite_only(self):
        self.config.scan('voteit.core.views.components.request_access')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.request_meeting_access()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_request_meeting_access_public(self):
        self.config.scan('voteit.core.views.components.request_access')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        self._load_vcs()
        context = self._fixture()
        context.set_field_value('access_policy', 'public')
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.request_meeting_access()
        self.assertIn('form', response)
        
    def test_request_meeting_access_all_participant_permissions(self):
        self.config.scan('voteit.core.views.components.request_access')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        self._load_vcs()
        context = self._fixture()
        context.set_field_value('access_policy', 'all_participant_permissions')
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.request_meeting_access()
        self.assertIn('form', response)
        
    def test_request_meeting_access_invalid_policy(self):
        self.config.scan('voteit.core.views.components.request_access')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        self._load_vcs()
        context = self._fixture()
        context.set_field_value('access_policy', 'fake_policy')
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.request_meeting_access()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_request_meeting_access_not_logged_in(self):
        self.config.scan('voteit.core.views.components.request_access')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(permissive=False)
        self._load_vcs()
        context = self._fixture()
        context.set_field_value('access_policy', 'all_participant_permissions')
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.request_meeting_access()
        self.assertIn('form', response)
        
    def test_presentation(self):
        self.config.scan('voteit.core.schemas.meeting')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.presentation()
        self.assertIn('form', response)
        
    def test_mail_settings(self):
        self.config.scan('voteit.core.schemas.meeting')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.mail_settings()
        self.assertIn('form', response)
        
    def test_access_policy(self):
        self.config.scan('voteit.core.views.components.request_access')
        self.config.scan('voteit.core.schemas.meeting')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.access_policy()
        self.assertIn('form', response)
        
    def test_global_poll_settings(self):
        self.config.scan('voteit.core.models.poll')
        self.config.scan('voteit.core.schemas.meeting')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.global_poll_settings()
        self.assertIn('form', response)
        
    def test_form(self):
        self.config.scan('voteit.core.schemas.meeting')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        
        from betahaus.pyracont.factories import createSchema
        schema = createSchema("PresentationMeetingSchema").bind(context=context, request=request)
        response = obj.form(schema)
        self.assertIn('form', response)
        
    def test_form_cancel(self):
        self.config.scan('voteit.core.schemas.meeting')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'}, is_xhr=False)
        obj = self._cut(context, request)
        
        from betahaus.pyracont.factories import createSchema
        schema = createSchema("PresentationMeetingSchema").bind(context=context, request=request)
        response = obj.form(schema)
        self.assertEqual(response.location, 'http://example.com/m/')

    def test_form_save(self):
        self.config.scan('voteit.core.schemas.meeting')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'save': 'save', 'title': 'Dummy Title', 'description': 'Dummy Description'}, is_xhr=False)
        obj = self._cut(context, request)
        
        from betahaus.pyracont.factories import createSchema
        schema = createSchema("PresentationMeetingSchema").bind(context=context, request=request)
        response = obj.form(schema)
        self.assertEqual(response.location, 'http://example.com/m/')

    def test_form_validation_error(self):
        self.config.scan('voteit.core.schemas.meeting')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'save': 'save', 'title': '', 'description': 'Dummy Description'}, is_xhr=False)
        obj = self._cut(context, request)
        
        from betahaus.pyracont.factories import createSchema
        schema = createSchema("PresentationMeetingSchema").bind(context=context, request=request)
        response = obj.form(schema)
        self.assertIn('form', response)

    def test_minutes(self):
        register_catalog(self.config)
        self.config.scan('voteit.core.subscribers.agenda_item')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()

        from voteit.core.models.agenda_item import AgendaItem
        context['a1'] = AgendaItem(title = 'Agenda Item 1')
        context['a1'].set_workflow_state(request, 'upcoming')
        context['a2'] = AgendaItem(title = 'Agenda Item 2')
        context['a2'].set_workflow_state(request, 'upcoming')
        context['a3'] = AgendaItem(title = 'Agenda Item 3')
        context['a3'].set_workflow_state(request, 'upcoming')
        
        obj = self._cut(context, request)
        response = obj.minutes()
        self.assertIn('agenda_items', response)
