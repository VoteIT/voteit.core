import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_security_policies
from voteit.core.testing_helpers import register_catalog
from voteit.core.testing_helpers import active_poll_fixture


class SearchViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.api import APIView
        return APIView

    def test_authn_policy(self):
        self.config.testing_securitypolicy('dummy')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.authn_policy)

    def test_authz_policy(self):
        self.config.testing_securitypolicy('dummy')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.authz_policy)

    def test_dt_util(self):
        self.config.registry.settings['default_timezone_name'] = 'Europe/Stockholm'
        self.config.include('voteit.core.models.date_time_util')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.dt_util)

    def test_user_profile(self):
        root = bootstrap_and_fixture(self.config)
        self.config.testing_securitypolicy('admin')
        request = testing.DummyRequest()
        obj = self._cut(root, request)
        self.assertTrue(obj.user_profile)

    def test_flash_messages(self):
        self.config.include('voteit.core.models.flash_messages')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.flash_messages)

    def test_show_moderator_actions(self):
        #FIXME: We still need a functional test for this
        root = bootstrap_and_fixture(self.config)
        self.config.testing_securitypolicy('admin', permissive = True)
        request = testing.DummyRequest()
        obj = self._cut(root, request)
        self.assertTrue(obj.show_moderator_actions)

    def test_localizer(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        from pyramid.i18n import Localizer
        self.assertIsInstance(obj.localizer, Localizer)

    def test_translate(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        from pyramid.i18n import TranslationString
        dummy_ts = TranslationString("Hello")
        obj = self._cut(context, request)
        res = obj.translate(dummy_ts)
        self.assertIsInstance(res, unicode)
        self.assertNotIsInstance(res, TranslationString)

    def test_pluralize(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertEqual(obj.pluralize('Singular', 'Plural', 1), 'Singular')
        self.assertEqual(obj.pluralize('Singular', 'Plural', 2), 'Plural')

    def test_context_unread(self):
        register_catalog(self.config)
        self.config.testing_securitypolicy('admin', permissive = True)
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.discussion_post import DiscussionPost
        root['m'] = Meeting()
        ai = root['m']['ai'] = AgendaItem()
        ai['d1'] = DiscussionPost()
        ai['d2'] = DiscussionPost()
        request = testing.DummyRequest()
        obj = self._cut(ai, request)
        self.assertEqual(len(obj.context_unread), 2)

    def test_register_form_resources(self):
        import colander
        import deform
        class DummySchema(colander.Schema):
            dummy = colander.SchemaNode(colander.String())
        dummy_form = deform.Form(DummySchema())

        from fanstatic import get_needed
        from fanstatic import init_needed
        from fanstatic import NeededResources
        init_needed() #Otherwise fanstatic won't get a proper needed resrouces object.
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        obj.register_form_resources(dummy_form)
        needed_resources = get_needed()
        self.assertIsInstance(needed_resources, NeededResources)
        filenames = [x.filename for x in needed_resources.resources()]
        #Note: Can be any filename registered by VoteIT. Just change it if this test fails :)
        self.assertIn('deform.css', filenames)

    def test_tstring(self):
        from pyramid.i18n import TranslationString
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertIsInstance(obj.tstring('Hello'), TranslationString)

    def test_get_user(self):
        root = bootstrap_and_fixture(self.config)
        request = testing.DummyRequest()
        obj = self._cut(root, request)
        self.failIf(hasattr(request, '_user_lookup_cache'))
        user = obj.get_user('admin')
        from voteit.core.models.interfaces import IUser
        self.failUnless(IUser.providedBy(user))
        self.assertEqual(user, request._user_lookup_cache['admin'])

    def test_get_meeting_outside_meeting(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertEqual(obj.meeting, None)

    def test_get_meeting_inside_meeting(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        meeting = root['m'] = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(meeting, request)
        self.assertEqual(obj.meeting, meeting)

    def test_meeting_state(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        meeting = root['m'] = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(meeting, request)
        self.assertEqual(obj.meeting_state, u'upcoming')

    def test_meeting_url(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        meeting = root['m'] = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(meeting, request)
        #example.com is from Pyramids testing env
        self.assertEqual(obj.meeting_url, 'http://example.com/m/')

    def test_get_moderator_actions(self):
        #Actual test of the view rendering should be part of that views test.
        self.config.testing_securitypolicy('admin', permissive = True)
        self.config.scan('voteit.core.views.components.moderator_actions')
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        meeting = root['m'] = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(meeting, request)
        self.assertIn('cogwheel', obj.get_moderator_actions(meeting))

    def test_get_time_created(self):
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.include('voteit.core.models.date_time_util')
        from voteit.core.models.date_time_util import utcnow
        context = testing.DummyResource()
        context.created = utcnow()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertEqual(obj.get_time_created(context), 'Just now')

    def test_get_userinfo_url(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        meeting = root['m'] = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(meeting, request)
        #example.com is from Pyramids testing suite
        self.assertEqual(obj.get_userinfo_url('somebody'), 'http://example.com/m/_userinfo?userid=somebody')

    def test_get_creators_info(self):
        #Functional test for view component should be in its own test
        self.config.scan('voteit.core.views.components.creators_info')
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        meeting = root['m'] = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(meeting, request)
        res = obj.get_creators_info(['admin'])
        self.assertIn('http://example.com/m/_userinfo?userid=admin', res)

    def test_context_has_permission(self):
        #Delegating function, we don't need to test it properly.
        self.config.testing_securitypolicy('admin', permissive = True)
        def _get_groups(dummy):
            return []
        context = testing.DummyResource()
        context.get_groups = _get_groups
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.context_has_permission('Dummy', context))

    def test_context_effective_principals(self):
        #Also a delegating function - actual test is in voteit.core.security
        self.config.testing_securitypolicy('admin', permissive = True)
        def _get_groups(dummy):
            return ['Hello']
        context = testing.DummyResource()
        context.get_groups = _get_groups
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        res = obj.context_effective_principals(context)
        self.assertEqual(res, ['system.Everyone', 'system.Authenticated', 'admin', 'Hello'])

    def test_is_brain_unread(self):
        register_catalog(self.config)
        self.config.testing_securitypolicy('admin', permissive = True)
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.discussion_post import DiscussionPost
        root['m'] = Meeting()
        ai = root['m']['ai'] = AgendaItem()
        ai['d1'] = DiscussionPost(title = 'Hello world')
        ai['d2'] = DiscussionPost()
        request = testing.DummyRequest()
        obj = self._cut(ai, request)
        from voteit.core.models.catalog import metadata_for_query
        d1_brain = metadata_for_query(root.catalog, title = 'Hello world')[0]
        self.assertTrue(obj.is_brain_unread(d1_brain))

    def test_get_restricted_content(self):
        #The get_content function doesn't need testing here
        #Fixture
        from voteit.core.models.base_content import BaseContent
        root = BaseContent()
        root['1'] = BaseContent()
        self.config.testing_securitypolicy('admin', permissive = True)
        request = testing.DummyRequest()
        obj = self._cut(root, request)
        self.assertEqual(obj.get_restricted_content(root)[0], root['1'])
        self.config.testing_securitypolicy('admin', permissive = False)
        request = testing.DummyRequest()
        obj = self._cut(root, request) #Reregister to use new request
        self.assertEqual(obj.get_restricted_content(root), [])

    def test_search_catalog(self):
        register_catalog(self.config)
        self.config.testing_securitypolicy('admin', permissive = True)
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.meeting import Meeting
        root['m'] = Meeting(title = 'Hello world')
        root['m2'] = Meeting(title = 'Goodbye')
        request = testing.DummyRequest()
        obj = self._cut(root, request)
        self.assertEqual(obj.search_catalog(title = 'Hello world')[0], 1)
        #Context search should remove the result if the context is another tree
        self.assertEqual(obj.search_catalog(context = root['m2'], title = 'Hello world')[0], 0)

    def test_resolve_catalog_docid(self):
        register_catalog(self.config)
        self.config.testing_securitypolicy('admin', permissive = True)
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.meeting import Meeting
        root['m'] = Meeting(title = 'Hello world')
        request = testing.DummyRequest()
        obj = self._cut(root, request)
        docid = root.catalog.search(title = 'Hello world')[1][0]
        self.assertEqual(obj.resolve_catalog_docid(docid), root['m'])

    def test_get_metadata_for_query(self):
        register_catalog(self.config)
        self.config.testing_securitypolicy('admin', permissive = True)
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.meeting import Meeting
        root['m'] = Meeting(title = 'Hello world')
        request = testing.DummyRequest()
        obj = self._cut(root, request)
        brain = obj.get_metadata_for_query(title = 'Hello world')[0]
        self.assertEqual(brain['title'], 'Hello world')

    def test_get_content_factory(self):
        self.config.scan('voteit.core.models.agenda_item')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        res = obj.get_content_factory('AgendaItem')
        from zope.component.factory import Factory
        self.assertIsInstance(res, Factory)

    def test_content_types_add_perm(self):
        self.config.scan('voteit.core.models.agenda_item')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        from voteit.core.security import ADD_AGENDA_ITEM
        self.assertEqual(obj.content_types_add_perm('AgendaItem'), ADD_AGENDA_ITEM)

    def test_get_schema_name(self):
        self.config.scan('voteit.core.models.agenda_item')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertEqual(obj.get_schema_name('AgendaItem', 'edit'), 'EditAgendaItemSchema')

    def test_render_view_group(self):
        self.config.scan('voteit.core.views.components.meeting')
        context = testing.DummyResource()
        context.description = 'Hello' #Just to make 'meeting_widgets' view group work
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertIn('description', obj.render_view_group(context, request, 'meeting_widgets'))

    def test_render_single_view_component(self):
        self.config.scan('voteit.core.views.components.meeting')
        context = testing.DummyResource()
        context.description = 'Hello' #Just to make 'meeting_widgets' view group work
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertIn('description', obj.render_single_view_component(context, request, 'meeting_widgets', 'description_richtext'))


_DUMMY_URL_MESSAGE = u"""Website: www.betahaus.net,
could be written as http://www.betahaus.net
Robins email is robin@betahaus.net"""
_DUMMY_URL_EXPECTED_RESULT = u"""Website: <a href="http://www.betahaus.net">www.betahaus.net</a>,<br />
could be written as <a href="http://www.betahaus.net">http://www.betahaus.net</a><br />
Robins email is <a href="mailto:robin@betahaus.net">robin@betahaus.net</a>"""

_DUMMY_MENTION_MESSAGE = u"""@admin
@test"""
_DUMMY_MENTION_EXPECTED_RESULT = u"""<a class="inlineinfo" href="/m/_userinfo?userid=admin" title="VoteIT Administrator">@admin</a><br />
@test"""

class TestTransform(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.api import APIView
        return APIView
    
    def _context(self):
        register_catalog(self.config)
        self.config.testing_securitypolicy('admin', permissive = True)
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.discussion_post import DiscussionPost
        root['m'] = Meeting()
        ai = root['m']['ai'] = AgendaItem()
        ai['d1'] = dp = DiscussionPost()
        return dp
    
    def test_newline_to_br(self):
        context = self._context()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        context.set_field_value('text', 'test\ntest')
        self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), unicode('test<br />\ntest'))

    def test_nl2br_several_runs_should_not_add_more_brs(self):
        context = self._context()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        context.title = "Hello\nthere"
        res = obj.transform(context.get_field_value('title'))
        context.title = res
        result = obj.transform(context.get_field_value('title'))
        self.assertEqual(result.count('<br />'), 1)

    def test_autolinking(self):
        context = self._context()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        context.set_field_value('text', _DUMMY_URL_MESSAGE)
        self.maxDiff = None
        self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_URL_EXPECTED_RESULT)

    def test_autolinking_several_runs(self):
        context = self._context()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        context.set_field_value('text', _DUMMY_URL_MESSAGE)
        first_run = obj.transform(context.get_field_value('text'))
        context.set_field_value('text', first_run)
        self.maxDiff = None
        self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_URL_EXPECTED_RESULT)
        
    def test_mention(self):
        context = self._context()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        context.set_field_value('text', _DUMMY_MENTION_MESSAGE)
        self.maxDiff = None
        self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_MENTION_EXPECTED_RESULT)

    def test_mention_several_runs(self):
        context = self._context()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        context.set_field_value('text', _DUMMY_MENTION_MESSAGE)
        first_run = obj.transform(context.get_field_value('text'))
        context.set_field_value('text', first_run)
        self.maxDiff = None
        self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_MENTION_EXPECTED_RESULT)
        
    def test_autolinking_mention(self):
        context = self._context()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        context.set_field_value('text', _DUMMY_URL_MESSAGE+"\n"+_DUMMY_MENTION_MESSAGE)
        self.maxDiff = None
        self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_URL_EXPECTED_RESULT+"<br />\n"+_DUMMY_MENTION_EXPECTED_RESULT)
        
    def test_autolinking_mention_several_runs(self):
        context = self._context()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        context.set_field_value('text', _DUMMY_URL_MESSAGE+"\n"+_DUMMY_MENTION_MESSAGE)
        first_run = obj.transform(context.get_field_value('text'))
        context.set_field_value('text', first_run)
        self.maxDiff = None
        self.assertEqual(unicode(obj.transform(context.get_field_value('text'))), _DUMMY_URL_EXPECTED_RESULT+"<br />\n"+_DUMMY_MENTION_EXPECTED_RESULT)