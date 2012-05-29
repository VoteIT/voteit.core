import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPForbidden
from pyramid_mailer import get_mailer

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
        from voteit.core.views.meeting import MeetingView
        return MeetingView
    
    def _fixture(self):
        """ Normal context for this view is an agenda item. """
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        return meeting

    def _load_vcs(self):
        self.config.scan('voteit.core.views.components.main')
        self.config.scan('voteit.core.views.components.meeting')
        
    def test_meeting_view(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.meeting_view()
        self.assertIn('meeting_columns', response)

    def test_meeting_view_no_permission(self):
        ''' View should redirect to request access view '''
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.meeting_view()
        self.assertEqual(response.location, 'http://example.com/m/@@request_access')
        
    def test_meeting_view_no_permission_not_loggedin(self):
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(permissive=False)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.meeting_view()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_participants_view(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.participants_view()
        self.assertIn('participants', response)
        
    def test_participants_emails(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.participants_emails()
        self.assertIn('participants', response)
        
    def test_claim_ticket(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertIn('form', response)
        
    def test_claim_ticket_not_logged_in(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(permissive=False)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertEqual(response.location, 'http://example.com/@@login?came_from=http%3A//example.com')
        
    def test_claim_ticket_post(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        from voteit.core.models.invite_ticket import InviteTicket
        ticket = InviteTicket('dummy@test.com', ['role:Moderator'], 'Welcome to the meeting!')
        ticket.__parent__ = context
        context.invite_tickets['dummy@test.com'] = ticket
        params = {'add': 'add', 'email': ticket.email, 'token': ticket.token}
        request = testing.DummyRequest(params=params, post=params)
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_claim_ticket_validation_error(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(params={'email': 'dummy@test.com', 'token': 'dummy_token'})
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertIn('form', response)
        
    def test_claim_ticket_get(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        from voteit.core.models.invite_ticket import InviteTicket
        ticket = InviteTicket('dummy@test.com', ['role:Moderator'], 'Welcome to the meeting!')
        ticket.__parent__ = context
        ticket.token = 'dummy_token'
        context.invite_tickets['dummy@test.com'] = ticket
        params = {'add': 'add', 'email': ticket.email, 'token': ticket.token}
        request = testing.DummyRequest(params=params)
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_claim_ticket_cancel(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.claim_ticket()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_add_tickets(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.email')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.add_tickets()
        self.assertIn('form', response)
        
    def test_add_tickets_cancel(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.add_tickets()
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_add_tickets_post(self):
        self.config.scan('voteit.core.models.invite_ticket')
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post = {'add': 'add', 
                                               'emails': 'dummy1@test.com\ndummy1@test.com', 
                                               'message': 'Welcome to the meeting!', 
                                               'roles': ['role:Moderator']})
        obj = self._cut(context, request)
        response = obj.add_tickets()
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_add_tickets_post_validation_error(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()

        request = testing.DummyRequest(post = {'add': 'add', 
                                               'emails': '', 
                                               'message': 'Welcome to the meeting!', 
                                               'roles': ['role:Moderator']})
        obj = self._cut(context, request)
        response = obj.add_tickets()

        self.assertIn('form', response)
        
    def test_manage_tickets(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.manage_tickets()
        self.assertIn('form', response)
        
    def test_manage_tickets_cancel(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.manage_tickets()
        self.assertEqual(response.location, 'http://example.com/m/')
        
    def test_manage_tickets_validation_error(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()

        request = testing.DummyRequest(post = {'resend': 'resend', 
                                               'emails': (),})
        obj = self._cut(context, request)
        response = obj.manage_tickets()

        self.assertIn('form', response)
        
    def test_manage_tickets_resend(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post = {'resend': 'resend', 
                                               'emails': ['dummy@test.com'],})
        from voteit.core.models.invite_ticket import InviteTicket
        ticket = InviteTicket('dummy@test.com', ['role:Moderator'], 'Welcome to the meeting!')
        ticket.__parent__ = context
        context.invite_tickets['dummy@test.com'] = ticket
        obj = self._cut(context, request)
        response = obj.manage_tickets()
        self.assertEqual(response.location, 'http://example.com/m/')
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        
    def test_manage_tickets_delete(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()

        request = testing.DummyRequest(post = {'delete': 'delete', 
                                               'emails': ['dummy@test.com'],})

        from voteit.core.models.invite_ticket import InviteTicket
        ticket = InviteTicket('dummy@test.com', ['role:Moderator'], 'Welcome to the meeting!')
        ticket.__parent__ = context
        context.invite_tickets['dummy@test.com'] = ticket
        obj = self._cut(context, request)
        response = obj.manage_tickets()
        self.assertEqual(response.location, 'http://example.com/m/')
        self.assertNotIn('dummy@test.com', context.invite_tickets)
        
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
                                           permissive=True)
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
                                           permissive=True)
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
                                           permissive=True)
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
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        context.set_field_value('access_policy', 'fake_policy')
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.request_meeting_access()
        self.assertEqual(response.location, 'http://example.com/')
        
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
        
    def test_form_cancel_with_ajax(self):
        self.config.scan('voteit.core.schemas.meeting')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'}, is_xhr=True)
        obj = self._cut(context, request)
        
        from betahaus.pyracont.factories import createSchema
        schema = createSchema("PresentationMeetingSchema").bind(context=context, request=request)
        response = obj.form(schema)
        self.assertIn(response.headers['X-Relocate'], 'http://example.com/m/')
        
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
        
    def test_form_save_with_ajax(self):
        self.config.scan('voteit.core.schemas.meeting')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'save': 'save', 'title': 'Dummy Title', 'description': 'Dummy Description'}, is_xhr=True)
        obj = self._cut(context, request)
        
        from betahaus.pyracont.factories import createSchema
        schema = createSchema("PresentationMeetingSchema").bind(context=context, request=request)
        response = obj.form(schema)
        self.assertIn(response.headers['X-Relocate'], 'http://example.com/m/')
        
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
        
    def test_form_validation_error_with_ajax(self):
        self.config.scan('voteit.core.schemas.meeting')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self._load_vcs()
        context = self._fixture()
        request = testing.DummyRequest(post={'save': 'save', 'title': '', 'description': 'Dummy Description'}, is_xhr=True)
        obj = self._cut(context, request)
        
        from betahaus.pyracont.factories import createSchema
        schema = createSchema("PresentationMeetingSchema").bind(context=context, request=request)
        response = obj.form(schema)
        self.assertEqual(response.status, '200 OK')
        self.assertIn("<legend>Presentation</legend>", response.text)
        
    def test_order_agenda_items(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.order_agenda_items()
        self.assertIn('title', response)
        
    def test_order_agenda_items_save(self):
        self.config.scan('voteit.core.subscribers.agenda_item')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        from voteit.core.models.agenda_item import AgendaItem
        context['a1'] = AgendaItem(title = 'Agenda Item 1')
        context['a2'] = AgendaItem(title = 'Agenda Item 2')
        context['a3'] = AgendaItem(title = 'Agenda Item 3')
        request = testing.DummyRequest(post = {'save': 'save', 
                                               'agenda_items': 'a1', 
                                               'agenda_items': 'a2', 
                                               'agenda_items': 'a3'},)
        obj = self._cut(context, request)
        response = obj.order_agenda_items()
        self.assertIn('title', response)
        
    def test_order_agenda_items_cancel(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self.config.include('voteit.core.models.flash_messages')
        context = self._fixture()
        request = testing.DummyRequest(post = {'cancel': 'cancel',})
        obj = self._cut(context, request)
        response = obj.order_agenda_items()
        self.assertEqual(response.location, 'http://example.com/m/')
        
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