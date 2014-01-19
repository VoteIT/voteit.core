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
                                                           ('add', 'add'),
                                                           ('csrf_token', '0123456789012345678901234567890123456789')]))
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
                                                           ('add', 'add'),
                                                           ('csrf_token', '0123456789012345678901234567890123456789')]))
        obj = self._cut(context, request)
        response = obj.add_form()
        self.assertIn('form', response)

    def test_view_user(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.registry.settings['default_locale_name'] = 'sv'
        self.config.include('voteit.core.models.date_time_util')
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        #self.config.scan('voteit.core.views.components.user_info')
        self.config.testing_securitypolicy(userid='dummy',
                                           permissive=True)
        users = self._fixture()
        context = users['dummy1'] 
        request = testing.DummyRequest(is_xhr=True)
        obj = self._cut(context, request)
        response = obj.view_user()
        #FIXME: Test rendering
