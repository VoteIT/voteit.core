# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest

from pyramid import testing
from arche.utils import resolve_docids

from voteit.core.bootstrap import bootstrap_voteit
from voteit.core.models.interfaces import IUnread
from voteit.core.testing_helpers import attach_request_method
from voteit.core.testing_helpers import bootstrap_and_fixture


class AtUseridLinkTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_chameleon')

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
        attach_request_method(request, creators_info, 'creators_info')
        attach_request_method(request, get_userinfo_url, 'get_userinfo_url')
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

    def _fixture(self):
        return testing.DummyModel(), testing.DummyRequest()

    def test_simple(self):
        value = self._fut("#hello world!", *self._fixture())
        self.assertIn('?tag=hello"', value)

    def test_non_ascii(self):
        value = self._fut('#åäöÅÄÖ', *self._fixture())
        self.assertIn('?tag=%C3%A5%C3%A4%C3%B6%C3%85%C3%84%C3%96', value)

    def test_several_tags_and_br(self):
        value = self._fut(u"Men #hörni, visst vore det väl trevligt med en #öl?", *self._fixture())
        self.assertIn('?tag=h%C3%B6rni', value)
        self.assertIn('?tag=%C3%B6l', value)

    def test_existing_tags_not_touched(self):
        value = self._fut('<a>#tag</a>', *self._fixture())
        self.assertEqual('<a>#tag</a>', value)

    def test_several_tags_twice(self):
        first = self._fut(u"Men #hörni, visst vore det väl trevligt med en #öl?", *self._fixture())
        second = self._fut(first, *self._fixture())
        self.assertEqual(first, second)

    def test_text_before_tag_negates_conversion(self):
        value = self._fut('this#that?', *self._fixture())
        self.assertEqual('this#that?', value)

    def test_html_entities(self):
        value = self._fut('this#that?', *self._fixture())
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
        self.assertEqual(truncated, 'Lorem ipsum<span class="trunc">&hellip;</span>')

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



class TestGetDocidsToShow(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
        self.config.testing_securitypolicy('admin', permissive = True)
        self.config.include('arche.testing')
        self.config.include('arche.models.catalog')
        self.config.include('voteit.core.models.catalog')
        self.config.include('voteit.core.models.unread')
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.discussion_post')
        self.config.include('voteit.core.models.site')
        self.config.include('voteit.core.models.users')
        self.config.include('voteit.core.models.user')
        self.config.include('voteit.core.testing_helpers.register_workflows')

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.helpers import get_docids_to_show
        return get_docids_to_show

    def _fixture(self, num = 10):
        root = bootstrap_voteit(echo = False)
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.discussion_post import DiscussionPost
        root['m'] = m = Meeting()
        for i in range(num):
            m['d%s' % i] = DiscussionPost()
        return root

    def _docid_structure(self, root, num = 10):
        res = []
        for i in range(num):
            res.append(root.document_map.docid_for_address("/m/d%s" % i))
        return res

    def _mark_read(self, root, items):
        for i in items:
            IUnread(root['m']['d%s' % i]).mark_as_read('admin')

    def _set_tag(self, root, items, tag = '#one'):
        for i in items:
            #To enable subscribers
            root['m']['d%s' % i].set_field_appstruct({'text': tag})

    def test_fixture(self):
        #Since it's kind of complex
        root = self._fixture(1)
        query = "unread == 'admin'"
        self.assertEqual(root.catalog.query(query)[0].total, 1)
        self.assertEqual(len(self._docid_structure(root, 1)), 1)

    def test_only_unread(self):
        root = self._fixture(6)
        request = testing.DummyRequest()
        request.root = root
        result = self._fut(root, request, 'DiscussionPost', limit = 3)
        docids = self._docid_structure(root)
        expected_batch = docids[0:3]
        expected_over = docids[3:6]
        self.assertEqual(expected_batch, result['batch'])
        self.assertEqual(expected_over, result['over_limit'])

    def test_too_many_unread(self):
        root = self._fixture(6)
        request = testing.DummyRequest()
        request.root = root
        self._mark_read(root, [0, 1])
        result = self._fut(root, request, 'DiscussionPost', limit = 2)
        docids = self._docid_structure(root, 6)
        expected_previous = docids[0:2]
        expected_batch = docids[2:4]
        expected_over = docids[4:6]
        expected_unread = docids[2:6]
        self.assertEqual(expected_previous, result['previous'])
        self.assertEqual(expected_batch, result['batch'])
        self.assertEqual(expected_over, result['over_limit'])
        self.assertEqual(expected_unread, result['unread'])

    def test_all_read(self):
        root = self._fixture(3)
        request = testing.DummyRequest()
        request.root = root
        self._mark_read(root, range(3))
        result = self._fut(root, request, 'DiscussionPost', limit = 2)
        docids = self._docid_structure(root)
        expected_previous = docids[0:1]
        expected_batch = docids[1:3]
        self.assertEqual(expected_previous, result['previous'])
        self.assertEqual(expected_batch, result['batch'])
        self.assertEqual([], result['over_limit'])

    def test_2_unread_fill_from_read(self):
        root = self._fixture()
        request = testing.DummyRequest()
        request.root = root
        self._mark_read(root, range(8))
        result = self._fut(root, request, 'DiscussionPost')
        docids = self._docid_structure(root)
        expected_previous = docids[0:5]
        expected_batch = docids[5:10]
        self.assertEqual(expected_batch, result['batch'])
        self.assertEqual(expected_previous, result['previous'])
        self.assertEqual([], result['over_limit'])

    def test_unread_gaps_dont_matter(self):
        root = self._fixture(6)
        request = testing.DummyRequest()
        request.root = root
        self._mark_read(root, [0, 2, 4])
        result = self._fut(root, request, 'DiscussionPost', limit = 4)
        docids = self._docid_structure(root, 6)
        expected_previous = docids[0:1]
        expected_batch = docids[1:5]
        expected_over = docids[5:6]
        expected_unread = [docids[1], docids[3], docids[5]]
        self.assertEqual(expected_batch, result['batch'])
        self.assertEqual(expected_previous, result['previous'])
        self.assertEqual(expected_over, result['over_limit'])
        self.assertEqual(expected_unread, result['unread'])

    def test_tags_matter(self):
        root = self._fixture()
        request = testing.DummyRequest()
        request.root = root
        self._mark_read(root, range(2))
        self._set_tag(root, range(6))
        result = self._fut(root, request, 'DiscussionPost', tags = ('one',), limit = 3)
        docids = self._docid_structure(root)
        expected_previous = docids[0:2]
        expected_batch = docids[2:5]
        expected_over = docids[5:6]
        self.assertEqual(expected_batch, result['batch'])
        self.assertEqual(expected_previous, result['previous'])
        self.assertEqual(expected_over, result['over_limit'])

    def test_disabled_limit_reads_all(self):
        root = self._fixture(5)
        request = testing.DummyRequest()
        request.root = root
        result = self._fut(root, request, 'DiscussionPost', limit = 0)
        docids = self._docid_structure(root, 5)
        self.assertEqual(docids, result['batch'])
        self.assertEqual([], result['previous'])
        self.assertEqual([], result['over_limit'])

    def test_start_after(self):
        root = self._fixture(5)
        request = testing.DummyRequest()
        request.root = root
        docids = self._docid_structure(root, 5)
        result = self._fut(root, request, 'DiscussionPost', limit = 5, start_after = docids[2])
        self.assertEqual(docids[3:], result['batch'])
        self.assertEqual([], result['previous'])
        self.assertEqual([], result['over_limit'])

    def test_end_before(self):
        root = self._fixture(5)
        request = testing.DummyRequest()
        request.root = root
        docids = self._docid_structure(root, 5)
        result = self._fut(root, request, 'DiscussionPost', limit = 5, end_before = docids[2])
        self.assertEqual(docids[:2], result['batch'])
        self.assertEqual([], result['previous'])
        self.assertEqual([], result['over_limit'])

    def test_start_and_end(self):
        root = self._fixture(5)
        request = testing.DummyRequest()
        request.root = root
        docids = self._docid_structure(root, 5)
        result = self._fut(root, request, 'DiscussionPost', limit = 5, start_after = docids[1], end_before = docids[3])
        self.assertEqual([docids[2]], result['batch'])
        self.assertEqual([], result['previous'])
        self.assertEqual([], result['over_limit'])


class TestGetDocidsToShow(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
        self.config.testing_securitypolicy('admin', permissive = True)
        self.config.include('arche.testing')
        self.config.include('arche.models.catalog')
        self.config.include('voteit.core.models.catalog')
        self.config.include('voteit.core.models.unread')
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.discussion_post')
        self.config.include('voteit.core.models.site')
        self.config.include('voteit.core.models.users')
        self.config.include('voteit.core.models.user')
        self.config.include('voteit.core.testing_helpers.register_workflows')

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.helpers import get_polls_struct
        return get_polls_struct

    def _fixture(self):
        root = bootstrap_voteit(echo = False)
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.poll import Poll
        root['m'] = m = Meeting()
        m['p1'] = Poll(title = 'Hello from one')
        m['p2'] = Poll(title = 'Hello from two')
        m['p3'] = Poll(title = 'Hello from three')
        request = testing.DummyRequest()
        request.root = root
        request.meeting = m
        request.is_moderator = False
        attach_request_method(request, resolve_docids, 'resolve_docids')
        return m, request

    def test_states_in_result(self):
        meeting, request = self._fixture()
        res = self._fut(meeting, request)
        self.assertEqual(len(res), 3)
        request.is_moderator = True
        res = self._fut(meeting, request)
        self.assertEqual(len(res), 4)

    def test_results_respect_limit(self):
        meeting, request = self._fixture()
        request.is_moderator = True
        res = self._fut(meeting, request, limit = 2)
        self.assertEqual(len(tuple(res[3]['polls'])), 2)
        self.assertEqual(res[3]['over_limit'], 1)
