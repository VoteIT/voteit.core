# import unittest
# from datetime import datetime
# from calendar import timegm
# 
# from pyramid import testing
# from pyramid.authentication import AuthTktAuthenticationPolicy
# from pyramid.authorization import ACLAuthorizationPolicy
# from pyramid.traversal import resource_path
# from zope.component.event import objectEventNotify
# from zope.interface.verify import verifyClass
# from zope.interface.verify import verifyObject
# 
# from voteit.core import security
# from voteit.core.bootstrap import bootstrap_voteit
# from voteit.core.models.arche_compat import createContent
# from voteit.core.models.date_time_util import utcnow
# from voteit.core.models.interfaces import ICatalogMetadata
# from voteit.core.models.interfaces import IUnread
# from voteit.core.models.site import SiteRoot
# from voteit.core.security import groupfinder
# from voteit.core.testing_helpers import bootstrap_and_fixture
# 
# 
# class CatalogIndexTests(unittest.TestCase):
#     """ Make sure indexes work as expected. """
#     def setUp(self):
#         self.config = testing.setUp()
#         self.config.include('arche.testing')
#         self.config.include('arche.models.catalog')
#         self.config.include('voteit.core.models.meeting')
#         self.config.include('voteit.core.models.site')
#         #self.config.scan('voteit.core.models.agenda_template')
#         self.config.include('voteit.core.models.agenda_templates')
#         self.config.include('voteit.core.models.user')
#         self.config.include('voteit.core.models.users')
#         #self.config.scan('voteit.core.subscribers.catalog')
#         #self.config.include('voteit.core.models.user_tags')
#         self.config.include('voteit.core.models.catalog')
#         #self.config.scan('betahaus.pyracont.fields.password')
# 
#         self.root = bootstrap_voteit(echo=False)
#         self.query = self.root.catalog.query
#         self.search = self.root.catalog.search
#         self.get_metadata = self.root.document_map.get_metadata
#         self.config.include('voteit.core.testing_helpers.register_workflows')
# 
#     def tearDown(self):
#         testing.tearDown()
# 
#     def _add_mock_meeting(self):
#         obj = createContent('Meeting', title = 'Testing catalog',
#                             description = 'To check that everything works as expected.',
#                             uid = 'simple_uid', creators = ['demo_userid'])
#         obj.add_groups('admin', (security.ROLE_ADMIN, security.ROLE_MODERATOR,), event = False)
#         self.root['meeting'] = obj
#         return obj
# 
#     def _register_security_policies(self):
#         authn_policy = AuthTktAuthenticationPolicy(secret='secret',
#                                                    callback=groupfinder)
#         authz_policy = ACLAuthorizationPolicy()
#         self.config.setup_registry(authorization_policy=authz_policy, authentication_policy=authn_policy)
# 
#     def test_workflow_state(self):
#         self._add_mock_meeting()
#         self.assertEqual(self.query("workflow_state == 'upcoming'")[0], 1)
# 
#     def test_allowed_to_view(self):
#         self._register_security_policies()
#         obj = self._add_mock_meeting()
#         #Owners are not allowed to view meetings. It's exclusive for Admins / Moderators right now
#         self.assertEqual(self.query("allowed_to_view in any('404',) and path == '/meeting'")[0], 0)
#         self.assertEqual(self.query("allowed_to_view in any('role:Viewer',) and path == '/meeting'")[0], 1)
#         self.assertEqual(self.query("allowed_to_view in any('role:Admin',) and path == '/meeting'")[0], 1)
#         self.assertEqual(self.query("allowed_to_view in any('role:Moderator',) and path == '/meeting'")[0], 1)
# 
#     def test_view_meeting_userids(self):
#         self._register_security_policies()
#         #Must add a user to users folder too, otherwise the find_authorized_userids won't accept them as valid
#         self.root['users']['demo_userid'] = createContent('User')
#         obj = self._add_mock_meeting()
#         self.assertEqual(self.search(view_meeting_userids = 'demo_userid')[0], 1)
# 
#     def test_start_time(self):
#         obj = self._add_mock_meeting()
# 
#         now = utcnow()
#         now_unix = timegm(now.timetuple())
#         
#         #Shouldn't return anything
#         self.assertEqual(self.query("start_time == %s and path == '/meeting'" % now_unix)[0], 0)
#         qy = ("%s < start_time < %s and path == '/meeting'" % (now_unix-1, now_unix+1))
#         self.assertEqual(self.query(qy)[0], 0)
#         
#         #So let's set it and return stuff
#         obj.set_field_value('start_time', now)
#         from voteit.core.models.catalog import reindex_indexes
#         reindex_indexes(self.root.catalog)
#         
#         self.assertEqual(self.query("start_time == %s and path == '/meeting'" % now_unix)[0], 1)
#         qy = ("%s < start_time < %s and path == '/meeting'" % (now_unix-1, now_unix+1))
#         self.assertEqual(self.query(qy)[0], 1)
# 
#     def test_end_time(self):
#         obj = self._add_mock_meeting()
# 
#         now = utcnow()
#         now_unix = timegm(now.timetuple())
#         
#         obj.set_field_value('end_time', now)
#         from voteit.core.models.catalog import reindex_indexes
#         reindex_indexes(self.root.catalog)
#         
#         self.assertEqual(self.query("end_time == %s and path == '/meeting'" % now_unix)[0], 1)
#         qy = ("%s < end_time < %s and path == '/meeting'" % (now_unix-1, now_unix+1))
#         self.assertEqual(self.query(qy)[0], 1)
# 
#     def test_unread(self):
#         meeting = self._add_mock_meeting()
#         self._register_security_policies()
#         self.config.include('voteit.core.models.unread')
#         #Discussion posts are unread aware
#         from voteit.core.models.discussion_post import DiscussionPost
#         obj = DiscussionPost()
#         obj.title = 'Hello'
#         meeting['post'] = obj
#         
#         from voteit.core.models.catalog import reindex_indexes
#         reindex_indexes(self.root.catalog)
#         
#         self.assertEqual(self.search(unread='admin')[0], 1)
#         
#         unread = self.config.registry.queryAdapter(obj, IUnread)
#         unread.mark_as_read('admin')
#         
#         self.assertEqual(self.search(unread='admin')[0], 0)
# 
#     def test_like_userids(self):
#         meeting = self._add_mock_meeting()
#         from voteit.core.models.discussion_post import DiscussionPost
#         obj = DiscussionPost()
#         obj.title = 'Hello'
#         meeting['post'] = obj
#         
#         self.assertEqual(self.search(like_userids='admin')[0], 0)
#         
#         #Set like
#         from voteit.core.models.interfaces import IUserTags
#         user_tags = self.config.registry.getAdapter(obj, IUserTags)
#         user_tags.add('like', 'admin')
#         
#         self.assertEqual(self.search(like_userids='admin')[0], 1)
#         
#         user_tags.remove('like', 'admin')
#         self.assertEqual(self.search(like_userids='admin')[0], 0)
# 
# 
# # class CatalogMetadataTests(unittest.TestCase):
# #     """ Testcase for CatalogMetadata adapter. The metadata is covered in the catalog tests.
# #     """
# #     def setUp(self):
# #         self.config = testing.setUp()
# #         self.root = SiteRoot() #Contains a catalog
# # 
# #     def tearDown(self):
# #         testing.tearDown()
# # 
# #     @property
# #     def _cut(self):
# #         from voteit.core.models.catalog import CatalogMetadata
# #         return CatalogMetadata
# # 
# #     def _make_obj(self):
# #         from voteit.core.models.base_content import BaseContent
# #         return self._cut(BaseContent())
# # 
# #     def test_class_implementation(self):
# #         verifyClass(ICatalogMetadata, self._cut)
# # 
# #     def test_obj_implementation(self):
# #         obj = self._make_obj()
# #         verifyObject(ICatalogMetadata, obj)
# # 
# #     def test_add_and_get_metadata(self):
# #         obj = self._make_obj()
# #         
# #         dm = self.root.catalog.document_map
# #         
# #         doc_id = dm.add(resource_path(obj.context))
# #         dm.add_metadata(doc_id, obj())
# #         
# #         metadata = dm.get_metadata(doc_id)
# #         self.assertEqual(metadata['title'], obj.context.title)
# #         self.assertEqual(metadata['created'], obj.context.created)
# #         
# #     def test_returned_metadata(self):
# #         obj = self._make_obj()
# #         result = obj()
# #         
# #         self.assertEqual(result['title'], obj.context.title)
# #         self.assertEqual(result['created'], obj.context.created)
# 
# 
# class CatalogSubscriberTests(unittest.TestCase):
# 
#     def setUp(self):
#         self.config = testing.setUp()
#         self.config.include('arche.models.catalog')
#         self.config.include('voteit.core.models.catalog')
#         self.config.include('voteit.core.models.user_tags')
#         self.config.include('voteit.core.models.catalog')
# 
#     def tearDown(self):
#         testing.tearDown()
# 
#     def _fixture(self):
#         return bootstrap_and_fixture(self.config)
# 
#     @property
#     def _ai(self):
#         """ Has metadata enabled """
#         from voteit.core.models.agenda_item import AgendaItem
#         return AgendaItem
# 
#     def _metadata_for_query(self, root, **kw):
#         from voteit.core.models.catalog import metadata_for_query
#         return metadata_for_query(root.catalog, **kw)
#     
#     def test_object_added_catalog(self):
#         root = self._fixture()
#         text = 'New object'
#         root['new_obj'] = self._ai(title = text)
#         self.assertEqual(root.catalog.search(title = text)[0], 1)
#     
#     def test_object_added_metadata(self):
#         root = self._fixture()
#         text = 'New object'
#         root['new_obj'] = self._ai(title = text)
#         metadata = self._metadata_for_query(root, title = text)
#         self.assertEqual(metadata[0]['title'], text)
# 
#     def test_object_updated_wf_changed_catalog(self):
#         root = self._fixture()
#         request = testing.DummyRequest()
#         text = 'New object'
#         root['new_obj'] = self._ai(title = text)
#         root['new_obj'].set_workflow_state(request, 'upcoming')
#         self.assertEqual(root.catalog.search(title = text, workflow_state = 'upcoming')[0], 1)
# 
#     def test_object_updated_wf_changed_metadata(self):
#         root = self._fixture()
#         request = testing.DummyRequest()
#         text = 'New object'
#         root['new_obj'] = self._ai(title = text)
#         root['new_obj'].set_workflow_state(request, 'upcoming')
#         metadata = self._metadata_for_query(root, title = text, workflow_state = 'upcoming')
#         self.assertEqual(metadata[0]['workflow_state'], 'upcoming')
# 
#     def test_object_updated_from_appstruct_catalog(self):
#         root = self._fixture()
#         ai = self._ai(title = 'New object')
#         root['new_obj'] = ai
#         ai.set_field_appstruct({'title': 'New title'})
#         self.assertEqual(root.catalog.search(title = 'New title')[0], 1)
# 
#     def test_object_deleted_from_catalog(self):
#         root = self._fixture()
#         ai = self._ai(title = 'New object')
#         root['new_obj'] = ai
#         #Just to make sure
#         self.assertEqual(root.catalog.search(uid = ai.uid)[0], 1)
#         del root['new_obj']
#         self.assertEqual(root.catalog.search(uid = ai.uid)[0], 0)
# 
#     def test_object_deleted_from_metadata(self):
#         root = self._fixture()
#         ai = self._ai(title = 'New object')
#         root['new_obj'] = ai
#         #Just to make sure
#         self.failUnless(self._metadata_for_query(root, uid = ai.uid))
#         del root['new_obj']
#         self.failIf(self._metadata_for_query(root, uid = ai.uid))
# 
#     def test_update_contained_in_ai(self):
#         self.config.include('voteit.core.testing_helpers.register_security_policies')
#         from voteit.core.models.discussion_post import DiscussionPost
#         from voteit.core.models.meeting import Meeting
#         from voteit.core.models.user import User
#         root = self._fixture()
#         root['users']['john'] = User()
#         root['m'] = Meeting()
#         root['m'].add_groups('john', [security.ROLE_VIEWER])
#         root['m']['ai'] = ai = self._ai(title = 'New object')
#         ai['dp'] = dp = DiscussionPost()
#         #To make sure dp got catalogued
#         self.assertEqual(root.catalog.search(uid = dp.uid)[0], 1)
#         #The discussion post shouldn't be visible now, since the ai is private
#         self.assertEqual(root.catalog.search(uid = dp.uid, allowed_to_view = [security.ROLE_VIEWER])[0], 0)
#         #When the ai is made upcoming, it should be visible
#         security.unrestricted_wf_transition_to(ai, 'upcoming')
#         self.assertEqual(root.catalog.search(uid = dp.uid, allowed_to_view = [security.ROLE_VIEWER])[0], 1)
