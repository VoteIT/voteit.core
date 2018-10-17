# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase

import colander
from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core import security


def _fixture(config):
    from voteit.core.models.user import User
    from voteit.core.models.meeting import Meeting
    config.include('pyramid_chameleon')
    root = bootstrap_and_fixture(config)
    config.include('arche.testing.setup_auth')
    config.include('voteit.core.models.meeting')
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
    root['meeting'] = meeting = Meeting()
    meeting.add_groups('tester', [security.ROLE_DISCUSS, security.ROLE_PROPOSE, security.ROLE_VOTER, security.ROLE_VIEWER])
    meeting.add_groups('moderator', [security.ROLE_MODERATOR])
    return root


class AtEnabledTextAreaTests(TestCase):
    
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)

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
        root = _fixture(self.config)
        context = root['meeting']
        obj = self._cut(context)
        class _DummyNode(object):
            name = 'hello'
        self.assertEqual(obj(_DummyNode(), "@moderator says to @tester that this shouldn't be valid."), None)

    def test_with_nonexistent_user(self):
        root = _fixture(self.config)
        context = root['meeting']
        obj = self._cut(context)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "@moderator says that naming @nonexistent should raise Invalid")

    def test_with_user_outside_of_meeting_context(self):
        from voteit.core.models.user import User
        root = _fixture(self.config)
        context = root['meeting']
        #New user
        root.users['new'] = User()
        obj = self._cut(context)
        node = None
        self.assertRaises(colander.Invalid, obj, node, "@new doesn't exist in this meeting so this shouldn't work")
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


class NoHTMLValidatorTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.validators import no_html_validator
        return no_html_validator

    def test_normal_text(self):
        node = None
        self.assertEqual(self._fut(node, "Here's some normal text that should pass\nShouldn't it?"), None)

    def test_text_with_html(self):
        node = None
        self.assertRaises(colander.Invalid, self._fut, node, "<html> is not allowed")


class RichTextValidatorTests(TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.validators import richtext_validator
        return richtext_validator

    def test_normal_text(self):
        node = None
        self.assertEqual(self._fut(node, "Here's some <strong>normal</strong> html that should pass."), None)

    def test_text_with_html(self):
        node = None
        self.assertRaises(colander.Invalid, self._fut, node, "Here's some html with forbidden tags <script>alert('test');</script>that should <strong>not</strong> pass.")


def _dummy_default_deferred(*kw):
    from voteit.core import _ as MF
    return MF('Proposal')


class NotOnlyDefaultTextValidatorTests(TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.validators import NotOnlyDefaultTextValidator
        return NotOnlyDefaultTextValidator

    def _mk_one(self, context = testing.DummyModel(), default_deferred = _dummy_default_deferred):
        request = testing.DummyRequest()
        return self._cut(context, request, default_deferred)

#FIXME: Make a test with translations as well? Right now we're only testing EN

    def test_same_as_default(self):
        obj = self._mk_one()
        self.assertRaises(colander.Invalid, obj, None, 'Proposal')

    def test_clear(self):
        obj = self._mk_one()
        self.assertEqual(obj(None, 'Not the same'), None)


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

    def test_deferred_token_form_validator(self):
        from voteit.core.validators import deferred_token_form_validator
        from voteit.core.validators import TokenFormValidator
        from voteit.core.models.meeting import Meeting
        res = deferred_token_form_validator(None, {'context': Meeting()})
        self.failUnless(isinstance(res, TokenFormValidator))


class TagValidatorTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.validators import TagValidator
        return TagValidator

    def test_simple_words(self):
        validator = self._cut()
        self.assertIsNone(validator(None, "HelloWhatsUp"))
        self.assertIsNone(validator(None, "NotMuch"))
        self.assertIsNone(validator(None, "not-much"))
        self.assertIsNone(validator(None, "what_up"))

    def test_international(self):
        validator = self._cut()
        self.assertIsNone(validator(None, "åäö"))
        self.assertIsNone(validator(None, "你好"))

    def test_things_that_should_fail(self):
        validator = self._cut()
        self.assertRaises(colander.Invalid, validator, None, "Hello world")
        self.assertRaises(colander.Invalid, validator, None, "你 好")
        self.assertRaises(colander.Invalid, validator, None, "Hi!")
        self.assertRaises(colander.Invalid, validator, None, " hello")
