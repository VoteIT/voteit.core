import unittest

from pyramid import testing
from pyramid_mailer import get_mailer
from webob.multidict import MultiDict

from voteit.core.testing_helpers import bootstrap_and_fixture




class SiteFormViewTests(unittest.TestCase):
        
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.views.site import SiteFormView
        return SiteFormView
    
    def _fixture(self):
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root.users['dummy1'] = User(title='Dummy 1')
        root.users['dummy2'] = User(title='Dummy 2')
        root.users['dummy3'] = User(title='Dummy 3', email='dummy3@test.com')
        root.users['dummy3'].set_password('dummy1234')
        return root.users

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

    def test_logout(self):
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=False)
        users = self._fixture()
        context = users.__parent__
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        response = obj.logout()
        self.assertEqual(response.location, 'http://example.com/')
