# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


def _mock_helpers(request, helper, name):
    """ Register as a request method, they won't be active otherwise."""
    def _mock_request_method(*args, **kwargs):
        return helper(request, *args, **kwargs)
    setattr(request, name, _mock_request_method)


class AtUseridLinkTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_chameleon')
        self.config.commit()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import at_userid_link
        return at_userid_link
        
    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.helpers import creators_info
        from voteit.core.helpers import get_userinfo_url
        root = bootstrap_and_fixture(self.config)
        root['m'] = Meeting()
        request = testing.DummyRequest()
        request.meeting = root['m']
        _mock_helpers(request, creators_info, 'creators_info')
        _mock_helpers(request, get_userinfo_url, 'get_userinfo_url')
        return request

    def test_single(self):
        request = self._fixture()
        value = self._fut(request, '@admin')
        self.assertIn('href="http://example.com/m/__userinfo__/admin', value)

    def test_dont_convert_if_char_in_front(self):
        request = self._fixture()
        value = self._fut(request, '..@admin')
        self.assertNotIn('href="http://example.com/m/__userinfo__/admin', value)


class Tags2linksTests(unittest.TestCase):
    
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request = self.request)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import tags2links
        return tags2links

    def test_simple(self):
        value = self._fut("#hello world!")
        self.assertEqual('<a href="?tag=hello" class="tag">#hello</a> world!', value)

    def test_non_ascii(self):
        value = self._fut('#åäöÅÄÖ')
        self.assertIn('?tag=%C3%A5%C3%A4%C3%B6%C3%85%C3%84%C3%96', value)

    def test_several_tags_and_br(self):
        value = self._fut(u"Men #hörni, visst vore det väl trevligt med en #öl?")
        self.assertIn('Men <a href="?tag=h%C3%B6rni" class="tag">#h\xf6rni</a>,', value)
        self.assertIn('en <a href="?tag=%C3%B6l" class="tag">#\xf6l</a>?', value)

    def test_existing_tags_not_touched(self):
        value = self._fut('<a>#tag</a>')
        self.assertEqual('<a>#tag</a>', value)

    def test_several_tags_twice(self):
        first = self._fut(u"Men #hörni, visst vore det väl trevligt med en #öl?")
        second = self._fut(first)
        self.assertEqual(first, second)

    def test_text_before_tag_negates_conversion(self):
        value = self._fut('this#that?')
        self.assertEqual('this#that?', value)

    def test_html_entities(self):
        value = self._fut('this#that?')
        self.assertEqual('this#that?', value)


class StripAndTruncateTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import strip_and_truncate
        return strip_and_truncate

    def test_strip_and_truncate(self):
        text = "Lorem ipsum dolor"
        truncated = self._fut(text, 10)
        self.assertEqual(truncated, 'Lorem ipsum<span class="trunc">&ellip;</span>') 

    def test_strip_and_truncate_dont_touch(self):
        text = "Lorem ipsum dolor"
        truncated = self._fut(text, 20)
        self.assertEqual(truncated, 'Lorem ipsum dolor') 


# _DUMMY_URL_MESSAGE = u"""Website: www.betahaus.net,
# could be written as http://www.betahaus.net"""
# _DUMMY_URL_EXPECTED_RESULT = u"""Website: <a href="http://www.betahaus.net">www.betahaus.net</a>,<br />
# could be written as <a href="http://www.betahaus.net">http://www.betahaus.net</a>"""


# _DUMMY_TAG_MESSAGE = u"""#test"""
# _DUMMY_TAG_EXPECTED_RESULT = u"""<a href="?tag=test" class="tag">#test</a>"""


class TestTransformText(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import transform_text
        return transform_text


#     
#     def _context(self):
#         register_catalog(self.config)
#         self.config.testing_securitypolicy('admin', permissive = True)
#         root = bootstrap_and_fixture(self.config)
#         from voteit.core.models.meeting import Meeting
#         from voteit.core.models.agenda_item import AgendaItem
#         from voteit.core.models.discussion_post import DiscussionPost
#         root['m'] = Meeting()
#         ai = root['m']['ai'] = AgendaItem()
#         ai['d1'] = dp = DiscussionPost()
#         return dp

#     def test_autolinking(self):
#         context = self._context()
#         request = testing.DummyRequest()
#         obj = self._cut(context, request)
#         context.set_field_value('text', _DUMMY_URL_MESSAGE)
#         self.maxDiff = None
#         self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_URL_EXPECTED_RESULT)
# 
#     def test_autolinking_several_runs(self):
#         context = self._context()
#         request = testing.DummyRequest()
#         obj = self._cut(context, request)
#         context.set_field_value('text', _DUMMY_URL_MESSAGE)
#         first_run = obj.transform(context.get_field_value('text'))
#         context.set_field_value('text', first_run)
#         self.maxDiff = None
#         self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_URL_EXPECTED_RESULT)
# 
#     def test_tags(self):
#         context = self._context()
#         request = testing.DummyRequest()
#         obj = self._cut(context, request)
#         context.set_field_value('text', _DUMMY_TAG_MESSAGE)
#         self.maxDiff = None
#         self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_TAG_EXPECTED_RESULT)
# 
#     def test_tags_several_runs(self):
#         context = self._context()
#         request = testing.DummyRequest()
#         obj = self._cut(context, request)
#         context.set_field_value('text', _DUMMY_TAG_MESSAGE)
#         first_run = obj.transform(context.get_field_value('text'))
#         context.set_field_value('text', first_run)
#         self.maxDiff = None
#         self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_TAG_EXPECTED_RESULT)
#         
#     def test_all_together(self):
#         context = self._context()
#         request = testing.DummyRequest()
#         obj = self._cut(context, request)
#         context.set_field_value('text', _DUMMY_URL_MESSAGE+"\n"+_DUMMY_MENTION_MESSAGE+"\n"+_DUMMY_TAG_MESSAGE)
#         self.maxDiff = None
#         self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_URL_EXPECTED_RESULT+"<br />\n"+_DUMMY_MENTION_EXPECTED_RESULT+"<br />\n"+_DUMMY_TAG_EXPECTED_RESULT)
#         
#     def test_all_togetherseveral_runs(self):
#         context = self._context()
#         request = testing.DummyRequest()
#         obj = self._cut(context, request)
#         context.set_field_value('text', _DUMMY_URL_MESSAGE+"\n"+_DUMMY_MENTION_MESSAGE+"\n"+_DUMMY_TAG_MESSAGE)
#         first_run = obj.transform(context.get_field_value('text'))
#         context.set_field_value('text', first_run)
#         self.maxDiff = None
#         self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_URL_EXPECTED_RESULT+"<br />\n"+_DUMMY_MENTION_EXPECTED_RESULT+"<br />\n"+_DUMMY_TAG_EXPECTED_RESULT)
#         
#     def test_nonascii(self):
#         context = self._context()
#         request = testing.DummyRequest()
#         obj = self._cut(context, request)
#         context.set_field_value('text', 'ÅÄÖåäö')
#         self.assertEqual(obj.transform(context.get_field_value('text')), 'ÅÄÖåäö')
