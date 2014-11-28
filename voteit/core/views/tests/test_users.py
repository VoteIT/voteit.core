import unittest

from pyramid import testing
from pyramid_mailer import get_mailer
from webob.multidict import MultiDict

from voteit.core.testing_helpers import bootstrap_and_fixture


class ChangePasswordFormTests(unittest.TestCase):
         
    def setUp(self):
        self.config = testing.setUp()
 
    def tearDown(self):
        testing.tearDown()
     
    @property
    def _cut(self):
        from voteit.core.views.users import ChangePasswordForm
        return ChangePasswordForm

    def _fixture(self):
        from voteit.core.models.user import User
        self.config.scan('voteit.core.schemas.user')
        root = bootstrap_and_fixture(self.config)
        root['users']['dummy'] = user = User(password = 'hello')
        root['users']['other'] = User(password = 'world')
        return user

    def test_change_own_password(self):
        self.config.testing_securitypolicy('dummy', permissive = True)
        context = self._fixture()
        postdata = MultiDict([('current_password', 'hello'),
                              ('__start__', 'password:mapping'),
                              ('password', 'secret'),
                              ('password-confirm', 'secret'),
                              ('__end__', 'password:mapping'),
                              ('change', 'Change'),])
        request = testing.DummyRequest(method = 'POST', post = postdata)
        obj = self._cut(context, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/users/dummy/')

    def test_change_password_on_other_admin(self):
        self.config.testing_securitypolicy('dummy', permissive = True)
        context = self._fixture()
        other = context.__parent__['other']
        postdata = MultiDict([('__start__', 'password:mapping'),
                              ('password', 'secret'),
                              ('password-confirm', 'secret'),
                              ('__end__', 'password:mapping'),
                              ('change', 'Change'),])
        request = testing.DummyRequest(method = 'POST', post = postdata)
        obj = self._cut(other, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/users/other/')


class RequestPasswordFormTests(unittest.TestCase):
         
    def setUp(self):
        self.config = testing.setUp()
 
    def tearDown(self):
        testing.tearDown()
     
    @property
    def _cut(self):
        from voteit.core.views.users import RequestPasswordForm
        return RequestPasswordForm

    def _fixture(self):
        from voteit.core.models.user import User
        self.config.include('pyramid_mailer.testing')
        root = bootstrap_and_fixture(self.config)
        root['users']['dummy'] = user = User(password = 'hello', email = 'dummy@site.com')
        return root

    def test_request_pw_userid(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.scan('voteit.core.views.components.email')
        context = self._fixture()
        postdata = MultiDict([('userid_or_email', 'dummy'),
                              ('request', 'Request'),])
        request = testing.DummyRequest(method = 'POST', post = postdata)
        obj = self._cut(context, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/')
        mailer = get_mailer(request)
        self.assertTrue(mailer.outbox)

    def test_request_pw_email(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.scan('voteit.core.views.components.email')
        context = self._fixture()
        postdata = MultiDict([('userid_or_email', 'dummy@site.com'),
                              ('request', 'Request'),])
        request = testing.DummyRequest(method = 'POST', post = postdata)
        obj = self._cut(context, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/')
        mailer = get_mailer(request)
        self.assertTrue(mailer.outbox)


class TokenChangePasswordFormTests(unittest.TestCase):
         
    def setUp(self):
        self.config = testing.setUp()
 
    def tearDown(self):
        testing.tearDown()
     
    @property
    def _cut(self):
        from voteit.core.views.users import TokenChangePasswordForm
        return TokenChangePasswordForm

    def _fixture(self):
        self.config.include('pyramid_mailer.testing')
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root['users']['dummy'] = user = User(password = 'hello')
        request = testing.DummyRequest()
        user.new_request_password_token(request)
        return root

    def test_change_pw(self):
        self.config.scan('voteit.core.schemas.user')
        self.config.scan('voteit.core.views.components.email')
        root = self._fixture()
        user = root['users']['dummy']
        postdata = MultiDict([('__start__', 'password:mapping'),
                              ('password', 'secret'),
                              ('password-confirm', 'secret'),
                              ('__end__', 'password:mapping'),
                              ('token', user.__token__.token),
                              ('change', 'Change'),])
        request = testing.DummyRequest(method = 'POST',
                                       post = postdata)
        obj = self._cut(user, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/login')


class ManageConnectedProfilesFormTests(unittest.TestCase):
         
    def setUp(self):
        self.config = testing.setUp()
 
    def tearDown(self):
        testing.tearDown()
     
    @property
    def _cut(self):
        from voteit.core.views.users import ManageConnectedProfilesForm
        return ManageConnectedProfilesForm

    def _fixture(self):
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root['users']['dummy'] = user = User(password = 'hello')
        user.auth_domains['some_auth'] = 'blabla'
        request = testing.DummyRequest()
        return root

    def test_delete_connected(self):
        self.config.scan('voteit.core.schemas.user')
        root = self._fixture()
        user = root['users']['dummy']
        postdata = MultiDict([('__start__', 'auth_domains:sequence'),
                              ('checkbox', 'some_auth'),
                              ('__end__', 'auth_domains:sequence'),
                              ('delete', 'Delete'),])
        request = testing.DummyRequest(method = 'POST',
                                       post = postdata)
        obj = self._cut(user, request)
        obj.check_csrf = False
        response = obj()
        self.assertEqual(response.location, 'http://example.com/users/dummy/')
        self.assertNotIn('some_auth', user.auth_domains)


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
        self.config.testing_securitypolicy(userid='dummy', permissive=True)
        context = self._fixture()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.list_users()
        self.assertIn('users', response)
