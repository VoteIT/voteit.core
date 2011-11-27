import colander
import deform
from unittest import TestCase

from pyramid import testing
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_security_policies
from voteit.core.testing_helpers import register_workflows
from voteit.core import security


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
        register_security_policies(self.config)
        register_workflows(self.config)
        root = _fixture(self.config)
        context = root['meeting']
        obj = self._cut(context)
        node = None
        self.assertEqual(obj(node, "@admin says to @tester that this shouldn't be valid."), None)

    def test_with_nonexistent_user(self):
        register_security_policies(self.config)
        register_workflows(self.config)
        root = _fixture(self.config)
        context = root['meeting']
        obj = self._cut(context)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "@admin says that naming @nonexistent should raise Invalid")

    def test_with_user_outside_of_meeting_context(self):
        from voteit.core.models.user import User

        register_security_policies(self.config)
        register_workflows(self.config)
        root = _fixture(self.config)
        context = root['meeting']
        #New user
        root.users['new'] = User()
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
        register_security_policies(self.config)
        root = _fixture(self.config)
        obj = self._cut(root)
        node = None
        self.assertEqual(obj(node, "john_doe"), None)

    def test_existing_userid(self):
        register_security_policies(self.config)
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

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.invite_ticket import InviteTicket
        meeting = Meeting()

        ticket = InviteTicket('this@email.com', ['role:Moderator'], 'Welcome to the meeting!')
        meeting.invite_tickets['this@email.com'] = ticket
        return meeting

    def _token_schema(self):
        from voteit.core.schemas.invite_ticket import ClaimTicketSchema
        return ClaimTicketSchema()

    def test_wrong_context(self):
        self.assertRaises(AssertionError, self._cut, testing.DummyModel())

    def test_nonexistent_ticket(self):
        meeting = self._fixture()
        obj = self._cut(meeting)
        node = self._token_schema()
        self.assertRaises(colander.Invalid, obj, node, {'email': 'other@email.com'})

    def test_existing_email_wrong_token(self):
        meeting = self._fixture()
        obj = self._cut(meeting)
        node = self._token_schema()
        self.assertRaises(colander.Invalid, obj, node, {'email': 'this@email.com', 'token': "i don't exist"})

    def test_correct_token(self):
        meeting = self._fixture()
        token_value = meeting.invite_tickets['this@email.com'].token
        obj = self._cut(meeting)
        node = self._token_schema()
        self.assertEqual(obj(node, {'email': 'this@email.com', 'token': token_value}), None)


class GlobalExistingUserIdTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.validators import GlobalExistingUserId
        return GlobalExistingUserId

    def test_nonexisting_userid(self):
        context = _fixture(self.config)
        obj = self._cut(context)
        node = None
        self.assertRaises(colander.Invalid, obj, node, 'non_existing_userid')

    def test_existing_userid(self):
        context = _fixture(self.config)
        obj = self._cut(context)
        node = None
        self.assertEqual(obj(node, 'admin'), None)


class PasswordValidationTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.validators import password_validation
        return password_validation

    def test_pw_length_too_short(self):
        self.assertRaises(colander.Invalid, self._fut, None, '123')
    
    def test_pw_length_too_long(self):
        pw = "123456789".join(['0' for x in range(11)])
        self.assertRaises(colander.Invalid, self._fut, None, pw)
    
    def test_pw_length(self):
        self.assertEqual(self._fut(None, 'good password'), None)


class MultipleEmailValidatorTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.validators import multiple_email_validator
        return multiple_email_validator

    def test_single(self):
        self.assertEqual(self._fut(None, "one@two.com"), None)

    def test_single_w_bad_chars(self):
        self.assertRaises(colander.Invalid, self._fut, None, "\none@two.com hello! \n")

    def test_multiple_good(self):
        self.assertEqual(self._fut(None, "one@two.com\nthree@four.net\nfive@six.com"), None)

    def test_multiple_one_bad(self):
        self.assertRaises(colander.Invalid, self._fut, None, "one@two.com\nthree@four.net\nfive@six.com\none@two.com hello! \n")


class DeferredValidatorsTests(TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_deferred_at_enabled_text(self):
        from voteit.core.validators import deferred_at_enabled_text
        from voteit.core.validators import AtEnabledTextArea
        res = deferred_at_enabled_text(None, {'context': None})
        self.failUnless(isinstance(res, AtEnabledTextArea))

    def test_deferred_new_userid_validator(self):
        from voteit.core.validators import deferred_new_userid_validator
        from voteit.core.validators import NewUniqueUserID
        res = deferred_new_userid_validator(None, {'context': None})
        self.failUnless(isinstance(res, NewUniqueUserID))

    def test_deferred_unique_email_validator(self):
        from voteit.core.validators import deferred_unique_email_validator
        from voteit.core.validators import UniqueEmail
        res = deferred_unique_email_validator(None, {'context': None})
        self.failUnless(isinstance(res, UniqueEmail))

    def test_deferred_password_token_validator(self):
        from voteit.core.validators import deferred_password_token_validator
        from voteit.core.validators import CheckPasswordToken
        from voteit.core.models.user import User
        res = deferred_password_token_validator(None, {'context': User()})
        self.failUnless(isinstance(res, CheckPasswordToken))

    def test_deferred_token_form_validator(self):
        from voteit.core.validators import deferred_token_form_validator
        from voteit.core.validators import TokenFormValidator
        from voteit.core.models.meeting import Meeting
        res = deferred_token_form_validator(None, {'context': Meeting()})
        self.failUnless(isinstance(res, TokenFormValidator))

    def test_deferred_existing_userid_validator(self):
        from voteit.core.validators import deferred_existing_userid_validator
        from voteit.core.validators import GlobalExistingUserId
        res = deferred_existing_userid_validator(None, {'context': None})
        self.failUnless(isinstance(res, GlobalExistingUserId))

