from unittest import TestCase

import colander
from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from pyramid_mailer import get_mailer

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_security_policies
from voteit.core.testing_helpers import register_workflows
from voteit.core.models.interfaces import IAuthPlugin
from voteit.core import security
from .interfaces import IPasswordHandler


class PasswordAuthTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from .models import PasswordAuth
        return PasswordAuth

    def test_verify_class(self):
        self.failUnless(verifyClass(IAuthPlugin, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IAuthPlugin, self._cut(None, None)))

    def test_modify_login_schema(self):
        schema = colander.Schema()
        obj = self._cut(None, None) #Proper context and request not needed here
        obj.modify_login_schema(schema)
        self.assertEqual('password', schema['password'].name)
        from .schemas import deferred_login_password_validator
        self.assertEqual(schema.validator, deferred_login_password_validator)

    def test_modify_register_schema(self):
        schema = colander.Schema()
        obj = self._cut(None, None) #Proper context and request not needed here
        obj.modify_register_schema(schema)
        self.assertEqual('password', schema['password'].name)

    def test_login(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        obj = self._cut(context, request)
        obj.login({'userid': 'dummy', 'password': 'dummy'})
        #FIXME: Proper test


class PasswordHandlerTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from .models import PasswordHandler
        return PasswordHandler

    @property
    def _user(self):
        from voteit.core.models.user import User
        return User

    def test_verify_class(self):
        self.failUnless(verifyClass(IPasswordHandler, self._cut))

    def test_verify_obj(self):
        self.failUnless(verifyObject(IPasswordHandler, self._cut(None)))

    def test_new_pw_token(self):
        self.config.include('pyramid_mailer.testing')
        user = self._user()
        obj = self._cut(user)
        request = testing.DummyRequest()
        obj.new_pw_token(request)
        self.failUnless(obj.get_token())
    
    def test_new_pw_token_mailed(self):
        self.config.include('pyramid_mailer.testing')
        user = self._user()
        obj = self._cut(user)
        request = testing.DummyRequest()
        obj.new_pw_token(request)
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        msg = mailer.outbox[0]
        self.failUnless(obj.get_token()() in msg.html)

#    def test_remove_password_token(self):
#        if hasattr(self, '__pw_request_token__'):
#            delattr(self, '__pw_request_token__')

#     def test_token_validator(self, node, value):
#         token = self.get_token()
#         if not token or value != token():
#             raise colander.Invalid(node, _(u"Token doesn't match."))
#         if  utcnow() > token.expires:
#             raise colander.Invalid(node, _(u"Token doesn't match."))
# 
#     def test_get_token(self):
#         return getattr(self, '__pw_request_token__', None)



def _fixture(config):
    from voteit.core.models.user import User
    from voteit.core.models.meeting import Meeting
    root = bootstrap_and_fixture(config)
    tester = User(password = 'tester',
                  creators = ['tester'],
                  first_name = u'Tester',
                  email = "tester@voteit.se",)
    root.users['tester'] = tester
    moderator = User(password = 'moderator',
                     creators = ['moderator'],
                     first_name = u'Moderator',
                     email = "moderator@voteit.se",)
    root.users['moderator'] = moderator
    meeting = Meeting()
    meeting.add_groups('tester', [security.ROLE_DISCUSS, security.ROLE_PROPOSE, security.ROLE_VOTER])
    meeting.add_groups('moderator', [security.ROLE_MODERATOR])
    root['meeting'] = meeting
    return root

#FIXME: Full integration test with schema

# class CheckPasswordTokenTests(TestCase):
# 
#     def setUp(self):
#         self.config = testing.setUp()
#         self.config.scan('voteit.core.views.components.email')
# 
#     def tearDown(self):
#         testing.tearDown()
#     
#     @property
#     def _cut(self):
#         from .schemas import CheckPasswordToken
#         return CheckPasswordToken
# 
#     @property
#     def _pw_handler(self):
#         from .models import PasswordHandler
#         return PasswordHandler
# 
#     def test_wrong_context(self):
#         self.assertRaises(AssertionError, self._cut, testing.DummyModel())
# 
#     def test_no_data(self):
#         root = _fixture(self.config)
#         user = root.users['tester']
#         obj = self._cut(user)
#         node = None
#         self.assertRaises(colander.Invalid, obj, node, "")
# 
#     def test_valid_token(self):
#         #Scan of user package should have been performed in fixture
#         root = _fixture(self.config)
#         request = testing.DummyRequest()
#         self.config.include('pyramid_mailer.testing')
#         user = root.users['tester']
#         pw_handler = self._pw_handler(user)
#         pw_handler.new_request_password_token(request)
#         token_value = user.__token__()
#         obj = self._cut(user)
#         node = None
#         self.assertEqual(obj(node, token_value), None)
# 
#     def test_valid_token_wrong_string_entered(self):
#         #Scan of user package should have been performed in fixture
#         root = _fixture(self.config)
#         request = testing.DummyRequest()
#         self.config.include('pyramid_mailer.testing')
#         user = root.users['tester']
#         user.new_request_password_token(request)
#         obj = self._cut(user)
#         node = None
#         self.assertRaises(colander.Invalid, obj, node, "wrong value for token")

#FIXME: Full integration test with schema


class PasswordValidationTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from .schemas import password_validation
        return password_validation

    def test_pw_length_too_short(self):
        self.assertRaises(colander.Invalid, self._fut, None, '123')
    
    def test_pw_length_too_long(self):
        pw = "123456789".join(['0' for x in range(11)])
        self.assertRaises(colander.Invalid, self._fut, None, pw)
    
    def test_pw_length(self):
        self.assertEqual(self._fut(None, 'good password'), None)


class CurrentPasswordValidatorTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _cut(self):
        from .schemas import CurrentPasswordValidator
        from voteit.core.models.user import User
        self.config.scan('betahaus.pyracont.fields.password')
        user = User(password = 'Hello')
        return CurrentPasswordValidator(user)

    def test_good_pw(self):
        obj = self._cut()
        self.assertEqual(obj(None, 'Hello'), None)

    def test_bad_pw(self):
        obj = self._cut()
        self.assertRaises(colander.Invalid, obj, None, "Incorrect pw")


class LoginPasswordValidatorTests(TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from .schemas import LoginPasswordValidator
        return LoginPasswordValidator

    def _get_login_schema(self):
        from voteit.core.schemas.auth import LoginSchema
        class Schema(LoginSchema):
            password = colander.SchemaNode(colander.String())
        return Schema()

    def test_nonexistent_users(self):
        root = bootstrap_and_fixture(self.config)
        obj = self._cut(root)
        self.assertRaises(colander.Invalid, obj, self._get_login_schema(), {'userid': u'moderator', 'password': u'moderator'})

    def test_existing_user_wrong_password(self):
        root = _fixture(self.config)
        obj = self._cut(root)
        self.assertRaises(colander.Invalid, obj, self._get_login_schema(), {'userid': u'moderator', 'password': u'wrong'})

    def test_existing_user_correct_password(self):
        root = _fixture(self.config)
        obj = self._cut(root)
        self.assertEqual(obj(self._get_login_schema(), {'userid': u'moderator', 'password': u'moderator'}), None)


class DeferredValidatorsTests(TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_deferred_password_token_validator(self):
        from .schemas import deferred_password_token_validator
        from .schemas import CheckPasswordToken
        from voteit.core.models.user import User
        res = deferred_password_token_validator(None, {'context': User()})
        self.failUnless(isinstance(res, CheckPasswordToken))

    def test_deferred_current_password_validator(self):
        from .schemas import deferred_current_password_validator
        from .schemas import CurrentPasswordValidator
        from voteit.core.models.user import User
        context = User()
        res = deferred_current_password_validator(None, {'context': context})
        self.assertIsInstance(res, CurrentPasswordValidator)

    def test_deferred_deferred_login_password_validator(self):
        from .schemas import deferred_login_password_validator
        from .schemas import LoginPasswordValidator
        from voteit.core.models.site import SiteRoot
        context = SiteRoot()
        request = testing.DummyRequest()
        res = deferred_login_password_validator(None, {'context': context, 'request': request})
        self.assertIsInstance(res, LoginPasswordValidator)
