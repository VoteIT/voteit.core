import unittest

from pyramid import testing
from webob.multidict import MultiDict

from voteit.core.testing_helpers import bootstrap_and_fixture


class AuthViewTests(unittest.TestCase):
        
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.auth import AuthView
        return AuthView
    
    def _fixture(self):
        from voteit.core.models.user import User
        self.config.scan('voteit.core.schemas.auth') #Login / register form
        self.config.scan('voteit.core.models.auth') #Subscribers
        self.config.include('voteit.core.plugins.password_auth') #As a default
        root = bootstrap_and_fixture(self.config)
        root.users['dummy1'] = User(title='Dummy 1')
        root.users['dummy2'] = User(title='Dummy 2')
        root.users['dummy3'] = User(title='Dummy 3', email='dummy3@test.com')
        root.users['dummy3'].set_password('dummy1234')
        return root

    def test_login_view(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(context = context,
                                       matchdict = {'method': 'password'},
                                       user_agent='Dummy agent',
                                       params={'came_from': '/'})
        obj = self._cut(context, request)
        response = obj.login()
        self.assertIn('form', response)

    def test_login_userid(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(context = context,
                                       matchdict = {'method': 'password'},
                                       post = MultiDict([('userid', 'dummy3'),
                                                           ('password', 'dummy1234'),
                                                           ('csrf_token', '0123456789012345678901234567890123456789'),
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        self.config = testing.setUp(self.config.registry, request = request)
        obj = self._cut(context, request)
        response = obj.login()
        #self.assertEqual(response.location, 'http://example.com/')
        self.assertEqual(response.status, '302 Found') #Redirect from login
        
    def test_login_email(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(context = context,
                                       matchdict = {'method': 'password'},
                                       post = MultiDict([('userid', 'dummy3@test.com'),
                                                         ('password', 'dummy1234'),
                                                         ('csrf_token', '0123456789012345678901234567890123456789'),
                                                         ('login', 'login')]),
                                       user_agent='Dummy agent')
        self.config = testing.setUp(self.config.registry, request = request)
        obj = self._cut(context, request)
        response = obj.login()
        #self.assertEqual(response.location, 'http://example.com/')
        self.assertEqual(response.status, '302 Found') #Redirect from login

    def test_login_came_from(self):
        context = self._fixture()
        request = testing.DummyRequest(matchdict = {'method': 'password'},
                                       post = MultiDict([('userid', 'dummy3@test.com'),
                                                         ('password', 'dummy1234'),
                                                         ('came_from', 'dummy_url'),
                                                         ('csrf_token', '0123456789012345678901234567890123456789'),
                                                         ('login', 'login')]),
                                       user_agent='Dummy agent',
                                       context = context)
        self.config = testing.setUp(self.config.registry, request = request)
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        obj = self._cut(context, request)
        response = obj.login()
        self.assertEqual(response.location, 'dummy_url')
        self.assertEqual(response.status, '302 Found') #Redirect from login

    def test_login_validation_error(self):
        context = self._fixture()
        request = testing.DummyRequest(context = context,
                                       matchdict = {'method': 'password'},
                                       post = MultiDict([('userid', 'dummy3@test.com'),
                                                           ('password', ''),
                                                           ('came_from', 'dummy_url'),
                                                           ('login', 'login')]),
                                       user_agent='Dummy agent')
        self.config = testing.setUp(self.config.registry, request = request)
        obj = self._cut(context, request)
        response = obj.login()
        self.assertIn('error', response['form'])

    def test_login_unsupported_browser(self):
        self.config.scan('voteit.core.schemas.auth')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest(user_agent='Mozilla/4.0 (compatible; MSIE 7.0;)')
        obj = self._cut(context, request)
        response = obj.login()
        self.assertEqual(response.location, 'http://example.com/unsupported_browser')

    def test_register(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        self.config.include('voteit.core.models.flash_messages')
        context = self._fixture()
        request = testing.DummyRequest(context = context,
                                       matchdict = {'method': 'password'},
                                       post = MultiDict([('userid', 'dummy4'),
                                                           ('__start__', 'password:mapping'),
                                                           ('password', 'dummy1234'),
                                                           ('password-confirm', 'dummy1234'),
                                                           ('__end__', 'password:mapping'),
                                                           ('email', 'dummy@test.com'),
                                                           ('first_name', 'Dummy'),
                                                           ('last_name', 'Person'),
                                                           ('csrf_token', '0123456789012345678901234567890123456789'),
                                                           ('register', 'register')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.register()
        self.assertEqual(response.location, 'http://example.com/users/dummy4/') #Home when no meeting joined
        
    def test_register_came_from(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.include('voteit.core.models.flash_messages')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(context = context,
                                       matchdict = {'method': 'password'},
                                       post = MultiDict([('userid', 'dummy4'),
                                                           ('__start__', 'password:mapping'),
                                                           ('password', 'dummy1234'),
                                                           ('password-confirm', 'dummy1234'),
                                                           ('__end__', 'password:mapping'),
                                                           ('email', 'dummy@test.com'),
                                                           ('first_name', 'Dummy'),
                                                           ('last_name', 'Person'),
                                                           ('came_from', 'dummy_url'),
                                                           ('csrf_token', '0123456789012345678901234567890123456789'),
                                                           ('register', 'register')]),
                                       user_agent='Dummy agent')
        obj = self._cut(context, request)
        response = obj.register()
        self.assertEqual(response.location, 'dummy_url')
        
    def test_register_validation_error(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        context = self._fixture()
        request = testing.DummyRequest(context = context,
                                       matchdict = {'method': 'password'},
                                       post = MultiDict([('userid', 'dummy4'),
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
        response = obj.register()
        self.assertIn('error', response['form'])

    def test_logout(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.logout()
        self.assertEqual(response.location, 'http://example.com/')
