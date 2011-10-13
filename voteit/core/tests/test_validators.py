import colander
import deform
from unittest import TestCase

from betahaus.pyracont.factories import createContent
from pyramid import testing
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy


def _fixture(config):
    from voteit.core import security
    from voteit.core.bootstrap import bootstrap_voteit
    config.scan('voteit.core.models.site')
    config.scan('voteit.core.models.user')
    config.scan('voteit.core.models.users')
    config.scan('voteit.core.models.meeting')
    config.scan('betahaus.pyracont.fields.password')

    root = bootstrap_voteit(echo=False)
    
    tester = createContent('User',
                         password = 'tester',
                         creators = ['tester'],
                         first_name = u'Tester',
                         email = "tester@voteit.se",)
    root.users['tester'] = tester

    moderator = createContent('User',
                              password = 'moderator',
                              creators = ['moderator'],
                              first_name = u'Moderator',
                              email = "moderator@voteit.se",)
    root.users['moderator'] = moderator

    meeting = createContent('Meeting')
    meeting.add_groups('tester', [security.ROLE_DISCUSS, security.ROLE_PROPOSE, security.ROLE_VOTER])
    meeting.add_groups('moderator', [security.ROLE_MODERATOR])
    root['meeting'] = meeting
    return root

def _register_security_policies(config):
    from voteit.core.security import groupfinder
    authn_policy = AuthTktAuthenticationPolicy(secret='secret',
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    config.setup_registry(authorization_policy=authz_policy, authentication_policy=authn_policy)

def _register_workflows(config):
    config.include('pyramid_zcml')
    config.load_zcml('voteit.core:configure.zcml')


class AtEnabledTextAreaTests(TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.validators import AtEnabledTextArea
        return AtEnabledTextArea

    def test_normal_text(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        node = None
        self.assertEqual(obj(node, "Here's some normal text that should pass\nShouldn't it?"), None)

    def test_text_with_html(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "<html> is not allowed")

    def test_with_at_links(self):
        _register_security_policies(self.config)
        _register_workflows(self.config)
        root = _fixture(self.config)
        context = root['meeting']
        obj = self._cut(context)
        node = None
        self.assertEqual(obj(node, "@admin says to @tester that this shouldn't be valid."), None)

    def test_with_nonexistent_user(self):
        _register_security_policies(self.config)
        _register_workflows(self.config)
        root = _fixture(self.config)
        context = root['meeting']
        obj = self._cut(context)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "@admin says that naming @nonexistent should raise Invalid")

    def test_with_user_outside_of_meeting_context(self):
        _register_security_policies(self.config)
        _register_workflows(self.config)
        root = _fixture(self.config)
        context = root['meeting']
        #New user
        root.users['new'] = createContent('User')
        obj = self._cut(context)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "@new doesn't exist in this meeting so this shouldn't work")
#FIXME: Full integration test with schema


class NewUniqueUserIDTests(TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.validators import NewUniqueUserID
        return NewUniqueUserID
    
    def test_bad_chars(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "userid with spaces is a bad idea")
        self.assertRaises(colander.Invalid, obj, node, "or % <>")
        self.assertRaises(colander.Invalid, obj, node, "")
        self.assertRaises(colander.Invalid, obj, node, "ab") #3 is minimum
        self.assertRaises(colander.Invalid, obj, node, "_invalid_start")

    def test_working_userid(self):
        _register_security_policies(self.config)
        root = _fixture(self.config)
        obj = self._cut(root)
        node = None
        self.assertEqual(obj(node, "john_doe"), None)

    def test_existing_userid(self):
        _register_security_policies(self.config)
        root = _fixture(self.config)
        obj = self._cut(root)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "admin")
#FIXME: Full integration test with schema


class UniqueEmailIDTests(TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.validators import UniqueEmail
        return UniqueEmail

    def test_bad_address(self):
        context = testing.DummyModel()
        obj = self._cut(context)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "I'm no email address")
        
    def test_regular_email_in_users_context(self):
        root = _fixture(self.config)
        obj = self._cut(root.users)
        node = None
        self.assertEqual(obj(node, "unique@voteit.se"), None)

    def test_resubmitting_users_own_address(self):
        root = _fixture(self.config)
        obj = self._cut(root.users['moderator'])
        node = None
        self.assertEqual(obj(node, "moderator@voteit.se"), None)

    def test_already_existing_address(self):
        root = _fixture(self.config)
        obj = self._cut(root.users)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "moderator@voteit.se")

#FIXME: Full integration test with schema

class CheckPasswordTokenTests(TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.validators import CheckPasswordToken
        return CheckPasswordToken

    def test_wrong_context(self):
        self.assertRaises(AssertionError, self._cut, testing.DummyModel())

    def test_no_data(self):
        root = _fixture(self.config)
        user = root.users['tester']
        obj = self._cut(user)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "")

    def test_valid_token(self):
        #Scan of user package should have been performed in fixture
        root = _fixture(self.config)
        request = testing.DummyRequest()
        self.config.include('pyramid_mailer.testing')
        user = root.users['tester']
        user.new_request_password_token(request)
        
        token_value = user.__token__()
        obj = self._cut(user)
        node = None
        self.assertEqual(obj(node, token_value), None)

    def test_valid_token_wrong_string_entered(self):
        #Scan of user package should have been performed in fixture
        root = _fixture(self.config)
        request = testing.DummyRequest()
        self.config.include('pyramid_mailer.testing')
        user = root.users['tester']
        user.new_request_password_token(request)
        obj = self._cut(user)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "wrong value for token")

#FIXME: Full integration test with schema


class TokenFormValidatorTests(TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.validators import TokenFormValidator
        return TokenFormValidator

#FIXME: Full integration test with schema

class GlobalExistingUserIdTests(TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.validators import GlobalExistingUserId
        return GlobalExistingUserId
#FIXME: Full integration test with schema
