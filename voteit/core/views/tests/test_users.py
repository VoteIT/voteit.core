import unittest

from pyramid import testing
from pyramid_mailer import get_mailer
from webob.multidict import MultiDict

from voteit.core.testing_helpers import bootstrap_and_fixture


class UsersViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.users import UsersView
        return UsersView
    
    def _fixture(self):
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root.users['dummy1'] = User(title='Dummy 1')
        root.users['dummy2'] = User(title='Dummy 2')
        root.users['dummy3'] = User(title='Dummy 3')
        return root.users
        
    def test_list_users(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.list_users()
        self.assertIn('users', response)
        
    def test_view_user(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy1'] 
        request = testing.DummyRequest(is_xhr=True)
        obj = self._cut(context, request)
        response = obj.view_user()
        self.assertIn('user_info', response)
        
class UsersFormViewTests(unittest.TestCase):
        
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.users import UsersFormView
        return UsersFormView
    
    def _fixture(self):
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root.users['dummy1'] = User(title='Dummy 1')
        root.users['dummy2'] = User(title='Dummy 2')
        root.users['dummy3'] = User(title='Dummy 3', email='dummy3@test.com')
        root.users['dummy3'].set_password('dummy1234')
        return root.users
    
    def test_add_form(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertIn('form', response)
        
    def test_add_form_cancel(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertEqual(response.location, 'http://example.com/users/')
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Canceled',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_add_form_post(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(post = MultiDict([('userid', 'dummy4'), 
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('email', 'dummy@test.com'), 
                                                           ('first_name', 'Dummy'), 
                                                           ('last_name', 'Person'), 
                                                           ('came_from', '/'), 
                                                           ('add', 'add')]))
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertIn('dummy4', context)
        self.assertEqual(response.location, 'http://example.com/users/')
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Successfully added',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_add_form_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        # the values needs to be in order for password field to work
        request = testing.DummyRequest(post = MultiDict([('userid', 'dummy3'), 
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('email', 'dummy@test.com'), 
                                                           ('first_name', 'Dummy'), 
                                                           ('last_name', 'Person'), 
                                                           ('came_from', '/'), 
                                                           ('add', 'add')]))
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertIn('form', response)
        
    def test_password_form(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.password_form()
        self.assertIn('form', response)
        
    def test_password_form_admin(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='admin',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.password_form()
        self.assertIn('form', response)
        
    def test_password_form_cancel(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.password_form()
        self.assertEqual(response.location, 'http://example.com/users/dummy3/')
        
    def test_password_form_post(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        # the values needs to be in order for password field to work
        request = testing.DummyRequest(post = MultiDict([('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('update', 'update')]))
        obj = self._cut(context, request)
        response = obj.password_form()
        self.assertEqual(response.location, 'http://example.com/users/dummy3/')
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Password changed',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_password_form_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        # the values needs to be in order for password field to work
        request = testing.DummyRequest(post = MultiDict([('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234_'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('update', 'update')]))
        obj = self._cut(context, request)
        response = obj.password_form()
        self.assertIn('form', response)
        
    def test_token_password_change(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.token_password_change()
        self.assertEqual(response.location, 'http://example.com/')
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Invalid security token. Did you click the link in your email?',
                                  'close_button': True,
                                  'type': 'error'}])
    
    def test_token_password_change_get(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest(params={'token': 'dummy_token'})
        obj = self._cut(context, request)
        response = obj.token_password_change()
        self.assertIn('form', response)
        
    def test_token_password_change_cancel(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.token_password_change()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_token_password_change_post(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        from voteit.core.models.user import RequestPasswordToken
        context.__token__ = RequestPasswordToken()
        # the values needs to be in order for password field to work
        request = testing.DummyRequest(post = MultiDict([('token', context.__token__()),
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('change', 'change')]))
        obj = self._cut(context, request)
        response = obj.token_password_change()
        self.assertEqual(response.location, 'http://example.com/login')
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Password set. You may login now.',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_token_password_change_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy3']
        from voteit.core.models.user import RequestPasswordToken
        context.__token__ = RequestPasswordToken()
        # the values needs to be in order for password field to work
        request = testing.DummyRequest(post = MultiDict([('token', context.__token__()),
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234_'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('change', 'change')]))
        obj = self._cut(context, request)
        response = obj.token_password_change()
        self.assertIn('form', response)
        
    def test_login_or_register(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(user_agent='Dummy agent', params={'came_from': '/'})
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertIn('login_form', response)
        self.assertIn('reg_form', response)
        
    def test_login_or_register_unsupported_browser(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(user_agent='Mozilla/4.0 (compatible; MSIE 7.0;)')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'http://example.com/unsupported_browser')
        
    def test_login_or_register_login_userid(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = MultiDict([('userid', 'dummy3'),
                                                           ('password', 'dummy1234'), 
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_login_or_register_login_email(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = MultiDict([('userid', 'dummy3@test.com'),
                                                           ('password', 'dummy1234'), 
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_login_or_register_login_came_from(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = MultiDict([('userid', 'dummy3@test.com'),
                                                           ('password', 'dummy1234'),
                                                           ('came_from', 'dummy_url'),
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'dummy_url')
        
    def test_login_or_register_login_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = MultiDict([('userid', 'dummy3@test.com'),
                                                           ('password', ''),
                                                           ('came_from', 'dummy_url'),
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertIn('login_form', response)
        
    def test_login_or_register_login_failed(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = MultiDict([('userid', 'dummy3@test.com'),
                                                           ('password', 'dummy1234_'),
                                                           ('came_from', 'dummy_url'),
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertIn('login_form', response)
        self.assertIn('reg_form', response)
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Login failed.',
                                  'close_button': True,
                                  'type': 'error'}])
        
    def test_login_or_register_register(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = MultiDict([('userid', 'dummy4'), 
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('email', 'dummy@test.com'), 
                                                           ('first_name', 'Dummy'), 
                                                           ('last_name', 'Person'), 
                                                           ('register', 'register')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'http://example.com/login')
        
    def test_login_or_register_register_came_from(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = MultiDict([('userid', 'dummy4'), 
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('email', 'dummy@test.com'), 
                                                           ('first_name', 'Dummy'), 
                                                           ('last_name', 'Person'), 
                                                           ('came_from', 'dummy_url'), 
                                                           ('register', 'register')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertEqual(response.location, 'dummy_url')
        
    def test_login_or_register_register_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = MultiDict([('userid', 'dummy4'), 
                                                           ('__start__', 'password:mapping'), 
                                                           ('password', 'dummy1234'), 
                                                           ('password-confirm', 'dummy1234_'), 
                                                           ('__end__', 'password:mapping'), 
                                                           ('email', 'dummy@test.com'), 
                                                           ('first_name', 'Dummy'), 
                                                           ('last_name', 'Person'), 
                                                           ('came_from', 'dummy_url'), 
                                                           ('register', 'register')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.login_or_register()
        self.assertIn('reg_form', response)
        
    def test_request_password(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertIn('form', response)
        
    def test_request_password_cancel(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(post={'cancel': 'cancel'})
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertEqual(response.location, 'http://example.com/')
        
    def test_request_password_userid(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('voteit.core.models.flash_messages')
        self.config.include('pyramid_mailer.testing')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = {'request': 'request', 'userid_or_email': 'dummy3'})
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertEqual(response.location, 'http://example.com/')
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Email sent.',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_request_password_email(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.scan('voteit.core.views.components.email')
        self.config.include('voteit.core.models.flash_messages')
        self.config.include('pyramid_mailer.testing')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = {'request': 'request', 'userid_or_email': 'dummy3@test.com'})
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertEqual(response.location, 'http://example.com/')
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Email sent.',
                                  'close_button': True,
                                  'type': 'info'}])
        
    def test_request_password_validation_error(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = {'request': 'request', 'userid_or_email': ''})
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertIn('form', response)
        
    def test_request_password_not_found(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(post = {'request': 'request', 'userid_or_email': 'dummy4'})
        obj = self._cut(context, request)
        response = obj.request_password()
        self.assertIn('form', response)
        flash = [x for x in request.session.pop_flash()]
        self.assertEqual(flash, [{'msg': 'Username or email not found.',
                                  'close_button': True,
                                  'type': 'error'}])
        
    def test_logout(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.logout()
        self.assertEqual(response.location, 'http://example.com/')