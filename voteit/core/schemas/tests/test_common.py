import unittest
from datetime import datetime

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class CommonSchemaTests(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request = self.request)

    def tearDown(self):
        testing.tearDown()

    def test_deferred_default_start_time(self):
        from voteit.core.schemas.common import deferred_default_start_time as fut
        settings = self.config.registry.settings
        settings['default_locale_name'] = 'sv'
        settings['default_timezone_name'] = 'Europe/Stockholm'
        self.config.include('voteit.core.models.date_time_util')
        res = fut(None, {'request': self.request})
        self.assertIsInstance(res, datetime)
        self.assertTrue(hasattr(res, 'tzinfo'))

    def test_deferred_default_end_time(self):
        from voteit.core.schemas.common import deferred_default_end_time as fut
        settings = self.config.registry.settings
        settings['default_locale_name'] = 'sv'
        settings['default_timezone_name'] = 'Europe/Stockholm'
        self.config.include('voteit.core.models.date_time_util')
        res = fut(None, {'request': self.request})
        self.assertIsInstance(res, datetime)
        self.assertTrue(hasattr(res, 'tzinfo'))

    def test_deferred_default_user_fullname(self):
        from voteit.core.schemas.common import deferred_default_user_fullname as fut
        from voteit.core.views.api import APIView
        root = bootstrap_and_fixture(self.config)
        admin = root.users['admin']
        admin.set_field_value('first_name', 'Jane')
        admin.set_field_value('last_name', 'Doe')
        self.config.testing_securitypolicy(userid='admin')
        kw = {'api': APIView(root, self.request)}
        self.assertEqual(fut(None, kw), 'Jane Doe')
        self.config.testing_securitypolicy(userid='404')
        kw = {'api': APIView(root, self.request)}
        self.assertEqual(fut(None, kw), '')

    def test_deferred_default_user_email(self):
        from voteit.core.schemas.common import deferred_default_user_email as fut
        from voteit.core.views.api import APIView
        root = bootstrap_and_fixture(self.config)
        admin = root.users['admin']
        admin.set_field_value('email', 'hello_world@betahaus.net')
        self.config.testing_securitypolicy(userid='admin')
        kw = {'api': APIView(root, self.request)}
        self.assertEqual(fut(None, kw), 'hello_world@betahaus.net')
        self.config.testing_securitypolicy(userid='404')
        kw = {'api': APIView(root, self.request)}
        self.assertEqual(fut(None, kw), '')


class DeferredDefaultTagsTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.schemas.common import deferred_default_tags
        return deferred_default_tags

    def test_no_tags_context(self):
        self.assertEqual(self._fut(None, {'context': object()}), u"")

    def test_with_int_tags(self):
        from voteit.core.models.discussion_post import DiscussionPost
        context = DiscussionPost()
        context.add_tags("HELLO World")
        self.assertEqual(self._fut(None, {'context': context}), u"hello world")


class DeferredDefaultHashtagTextTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.schemas.common import deferred_default_hashtag_text
        return deferred_default_hashtag_text

    @property
    def _prop(self):
        from voteit.core.models.proposal import Proposal
        return Proposal

    def test_context_is_agenda_item(self):
        from voteit.core.models.agenda_item import AgendaItem
        context = AgendaItem()
        request = testing.DummyRequest()
        self.assertEqual(self._fut(None, {'context': context, 'request': request}), u"")

    def test_context_without_creators(self):
        #This is not the normal case
        context = self._prop()
        request = testing.DummyRequest()
        self.assertEqual(self._fut(None, {'context': context, 'request': request}), u"")

    def test_context_has_creators(self):
        context = self._prop(creators = ['jeff'])
        request = testing.DummyRequest()
        self.assertEqual(self._fut(None, {'context': context, 'request': request}), u"@jeff: ")

    def test_context_has_tags(self):
        #Tags without creator isn't the normal case
        context = self._prop()
        context.add_tags("HELLO World")
        request = testing.DummyRequest()
        self.assertEqual(self._fut(None, {'context': context, 'request': request}), u" #hello #world")

    def test_context_has_tags_and_creators(self):
        context = self._prop(creators = ['jeff'])
        context.add_tags("HELLO World")
        request = testing.DummyRequest()
        self.assertEqual(self._fut(None, {'context': context, 'request': request}), u"@jeff:  #hello #world")

    def test_context_has_tags_and_creators_and_request_has_tag(self):
        context = self._prop(creators = ['jeff'])
        context.add_tags("HELLO World")
        request = testing.DummyRequest(params = {'tag': 'me-is_tag-2'})
        self.assertEqual(self._fut(None, {'context': context, 'request': request}), u"@jeff:  #hello #world #me-is_tag-2")
