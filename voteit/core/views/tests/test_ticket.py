import unittest

from pyramid import testing
from pyramid_mailer import get_mailer
from pyramid.httpexceptions import HTTPForbidden
from webob.multidict import MultiDict

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core import security


class TicketViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.ticket import TicketView
        return TicketView

    @property
    def _make_ticket(self):
        from voteit.core.models.invite_ticket import InviteTicket
        return InviteTicket

    def _fixture(self):
        return _fixture(self.config)

    def _add_ticket(self, context):
        ticket = self._make_ticket('dummy@test.com', ['role:Moderator'], 'Welcome to the meeting!')
        ticket.__parent__ = context
        ticket.token = 'dummy_token'
        context.invite_tickets['dummy@test.com'] = ticket

    def test_ticket_redirect_anon(self):
        context = self._fixture()
        request = testing.DummyRequest(url=u"http://dummy.url") #Will be incoming ticket url
        obj = self._cut(context, request)
        response = obj.ticket_redirect()
        self.assertEqual(response.location, u"http://example.com/m/ticket_login?came_from=http%3A%2F%2Fdummy.url")

    def test_ticket_redirect_authenticated_no_ticket(self):
        self.config.testing_securitypolicy(userid='dummy', permissive=True)
        self.config.include('voteit.core.models.flash_messages')
        context = self._fixture()
        request = testing.DummyRequest(url=u"http://dummy.url") #Will be incoming ticket url
        obj = self._cut(context, request)
        response = obj.ticket_redirect()
        self.assertEqual(response.location, u"http://example.com/m/")
        messages = tuple(obj.api.flash_messages.get_messages())
        self.assertEqual(messages[0]['type'], 'error') #To check that there was a flash message displaying error
        self.assertEqual(response.location, u"http://example.com/m/")

    def test_ticket_redirect_authenticated_w_ticket(self):
        self.config.testing_securitypolicy(userid='dummy', permissive=True)
        self.config.include('voteit.core.models.flash_messages')
        context = self._fixture()
        request = testing.DummyRequest(url=u"http://dummy.url?email=dummy@test.com&token=dummy_token",
                                       params = {'email': 'dummy@test.com', 'token': 'dummy_token'}) #Will be incoming ticket url
        obj = self._cut(context, request)
        response = obj.ticket_redirect()
        self.assertEqual(response.location, u"http://example.com/m/ticket_claim?token=dummy_token&email=dummy%40test.com")   

    def test_ticket_login(self):
        context = self._fixture()
        request = testing.DummyRequest(params = {'came_from': 'dummy_test'})
        obj = self._cut(context, request)
        response = obj.ticket_login()
        self.assertEqual('dummy_test', response['came_from'])

    def test_ticket_claim_not_logged_in(self):
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertRaises(HTTPForbidden, obj.ticket_claim)

    def test_ticket_claim_just_view(self):
        self.config.testing_securitypolicy(userid='dummy', permissive=True)
        self.config.scan('voteit.core.schemas.invite_ticket')
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.ticket_claim()
        self.assertEqual(response['claim_action_url'], 'http://example.com/m/ticket_claim?claim=1&token=&email=')

    def test_ticket_claim_action(self):
        self.config.testing_securitypolicy(userid='dummy', permissive=True)
        self.config.include('voteit.core.models.flash_messages')
        self.config.scan('voteit.core.schemas.invite_ticket')
        context = self._fixture()
        self._add_ticket(context)
        request = testing.DummyRequest(url = u"http://dummy.url?email=dummy@test.com&token=dummy_token&claim=1",
                                       params = {'email': 'dummy@test.com', 'token': 'dummy_token', 'claim': '1'})
        obj = self._cut(context, request)
        response = obj.ticket_claim()
        fm = tuple(obj.api.flash_messages.get_messages())
        self.assertEqual(len(fm), 1)
        self.assertEqual(response.location, u'http://example.com/m/')
        self.assertEqual(context.invite_tickets['dummy@test.com'].get_workflow_state(), u'closed')

    def test_ticket_claim_validation_error(self):
        self.config.testing_securitypolicy(userid='dummy', permissive=True)
        self.config.include('voteit.core.models.flash_messages')
        self.config.scan('voteit.core.schemas.invite_ticket')
        context = self._fixture()
        self._add_ticket(context)
        request = testing.DummyRequest(url = u"http://dummy.url?email=dummy@test.com&token=wrong_token&claim=1",
                                       params = {'email': 'dummy@test.com', 'token': 'wrong_token', 'claim': '1'})
        obj = self._cut(context, request)
        response = obj.ticket_claim()
        fm = tuple(obj.api.flash_messages.get_messages())
        self.assertEqual(len(fm), 1)
        self.assertEqual(fm[0]['type'], 'error')
        self.assertEqual(response.location, u'http://example.com/')
        self.assertEqual(context.invite_tickets['dummy@test.com'].get_workflow_state(), u'open')

    def test_add_tickets(self):
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.tabs_menu')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.add_tickets()
        self.assertIn('form', response)

    def test_add_tickets_submit(self):
        self.config.scan('voteit.core.models.invite_ticket')
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.tabs_menu')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(post = {'add': 'add', 
                                               'emails': 'dummy1@test.com\ndummy2@test.com', 
                                               'message': 'Welcome to the meeting!', 
                                               'roles': ['role:Moderator'],
                                               'csrf_token': '0123456789012345678901234567890123456789'})
        obj = self._cut(context, request)
        response = obj.add_tickets()
        self.assertEqual(response.location, 'http://example.com/m/send_tickets')

    def test_add_tickets_submit_some_rejected(self):
        self.config.scan('voteit.core.models.invite_ticket')
        self.config.scan('voteit.core.schemas.invite_ticket')
        self.config.scan('voteit.core.views.components.tabs_menu')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        existing_ticket = context.add_invite_ticket('dummy1@test.com', [security.ROLE_DISCUSS])
        request = testing.DummyRequest(post = {'add': 'add', 
                                               'emails': 'dummy1@test.com\ndummy2@test.com',
                                               'message': 'Welcome to the meeting!', 
                                               'roles': ['role:Moderator'],
                                               'csrf_token': '0123456789012345678901234567890123456789'})
        obj = self._cut(context, request)
        response = obj.add_tickets()
        self.assertEqual(response.location, 'http://example.com/m/send_tickets')
        self.assertEqual(existing_ticket, context.invite_tickets['dummy1@test.com'])

    def test_manage_tickets(self):
        self.config.scan('voteit.core.models.invite_ticket')
        self.config.scan('voteit.core.views.components.tabs_menu')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        context.add_invite_ticket('john@doe.com', [security.ROLE_MODERATOR], sent_by = 'dummy')
        context.add_invite_ticket('jane@doe.com', [security.ROLE_MODERATOR], sent_by = 'dummy')
        obj = self._cut(context, request)
        response = obj.manage_tickets()
        self.assertEqual(2, len(response['invite_tickets']))

    def test_manage_tickets_resend(self):
        self.config.scan('voteit.core.models.invite_ticket')
        self.config.scan('voteit.core.views.components.tabs_menu')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        context.add_invite_ticket('john@doe.com', [security.ROLE_MODERATOR], sent_by = 'dummy')
        context.add_invite_ticket('jane@doe.com', [security.ROLE_MODERATOR], sent_by = 'dummy')
        request = testing.DummyRequest(post = MultiDict([('resend', 'Resend'),
                                                         ('message', 'Hello world'),
                                                        ('email', 'john@doe.com'),
                                                        ('email', 'jane@doe.com'),
                                                        ]))
        obj = self._cut(context, request)
        obj.manage_tickets()
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 2)

    def test_manage_tickets_resend_with_claimed(self):
        self.config.scan('voteit.core.models.invite_ticket')
        self.config.scan('voteit.core.views.components.tabs_menu')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        context.add_invite_ticket('john@doe.com', [security.ROLE_MODERATOR], sent_by = 'dummy')
        context.add_invite_ticket('jane@doe.com', [security.ROLE_MODERATOR], sent_by = 'dummy')
        request = testing.DummyRequest(post = MultiDict([('resend', 'Resend'),
                                                         ('message', 'Hello world'),
                                                        ('email', 'john@doe.com'),
                                                        ('email', 'jane@doe.com'),
                                                        ]))
        context.invite_tickets['jane@doe.com'].claim(request)
        obj = self._cut(context, request)
        obj.manage_tickets()
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)

    def test_manage_tickets_remove(self):
        self.config.scan('voteit.core.models.invite_ticket')
        self.config.scan('voteit.core.views.components.tabs_menu')
        #self.config.scan('voteit.core.views.components.email')
        #self.config.include('pyramid_mailer.testing')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        context.add_invite_ticket('john@doe.com', [security.ROLE_MODERATOR], sent_by = 'dummy')
        context.add_invite_ticket('jane@doe.com', [security.ROLE_MODERATOR], sent_by = 'dummy')
        request = testing.DummyRequest(post = MultiDict([('remove', 'Remove'),
                                                        ('email', 'john@doe.com'),
                                                        ('email', 'jane@doe.com'),
                                                        ]))
        obj = self._cut(context, request)
        obj.manage_tickets()
        self.assertEqual(len(context.invite_tickets), 0)


class SendTicketsActionTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()
        self.config.scan('voteit.core.models.invite_ticket')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('pyramid_mailer.testing')

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.views.ticket import send_tickets_action
        return send_tickets_action

    def test_send_tickets_action(self):
        context = _fixture(self.config)
        _mk_invites(context)
        request = testing.DummyRequest()
        request.session['send_tickets.emails'] = ['invite1@voteit.se']
        request.session['send_tickets.message'] = 'Hello'
        response = self._fut(context, request)
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(len(context.invite_tickets['invite1@voteit.se'].sent_dates), 1)
        self.assertEqual(response, {'remaining': 0, 'sent': 1})

    def test_send_tickets_action_only_does_20(self):
        context = _fixture(self.config)
        _mk_invites(context, count = 21)        
        request = testing.DummyRequest()
        request.session['send_tickets.message'] = 'Hello'
        request.session['send_tickets.emails'] = list(context.invite_tickets.keys())
        self.assertEqual(len(request.session['send_tickets.emails']), 21) #Just to make sure
        response = self._fut(context, request)
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 20)
        self.assertEqual(len(context.invite_tickets['invite5@voteit.se'].sent_dates), 1)
        self.assertEqual(response['sent'], 20)


def _fixture(config):
    from voteit.core.models.meeting import Meeting
    from voteit.core.models.user import User
    root = bootstrap_and_fixture(config)
    root['m'] = meeting = Meeting()
    root.users['dummy'] = User()
    return meeting

def _mk_invites(context, count = 1, roles = [security.ROLE_MODERATOR]):
    while count:
        context.add_invite_ticket('invite%s@voteit.se' % count, roles)
        count -= 1

# @view_config(name = "send_tickets", context = IMeeting, renderer = "json", permission = security.MANAGE_GROUPS, xhr = True)
# def send_tickets_action(context, request):
#     result = []
#     post_vars = request.POST.dict_of_lists()
#     for email in post_vars.get('emails', ()):
#         context.invite_tickets[email].send(request)
#         result.append(email)
#         if len(result) > 19:
#             break
#     return {'sent': len(result), 'emails': result}
