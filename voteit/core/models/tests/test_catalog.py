import unittest
from datetime import datetime
from calendar import timegm

from pyramid import testing
from pyramid.security import principals_allowed_by_permission
from pyramid.security import remember
from zope.interface.verify import verifyObject
from zope.component.event import objectEventNotify
from betahaus.pyracont.factories import createContent
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import AuthTktAuthenticationPolicy

from voteit.core.bootstrap import bootstrap_voteit
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core.events import ObjectUpdatedEvent
from voteit.core import security
from voteit.core.security import groupfinder
from voteit.core.models.date_time_util import utcnow


class CatalogTestCase(unittest.TestCase):
    """ Class for registering test setup and some helper methods.
        This doesn't actually run any tests.
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.scan('voteit.core.models.meeting')
        self.config.scan('voteit.core.models.site')
        self.config.scan('voteit.core.models.user')
        self.config.scan('voteit.core.models.users')
        self.config.scan('voteit.core.subscribers.catalog')
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.catalog')
        self.config.scan('betahaus.pyracont.fields.password')

        self.root = bootstrap_voteit(echo=False)
        self.query = self.root.catalog.query
        self.search = self.root.catalog.search
        self.get_metadata = self.root.catalog.document_map.get_metadata
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()

    def _add_mock_meeting(self):
        obj = createContent('Meeting', title = 'Testing catalog',
                            description = 'To check that everything works as expected.',
                            uid = 'simple_uid', creators = ['demo_userid'])
        obj.add_groups('admin', (security.ROLE_ADMIN, security.ROLE_MODERATOR,))
        self.root['meeting'] = obj
        return obj

    def _register_security_policies(self):
        authn_policy = AuthTktAuthenticationPolicy(secret='secret',
                                                   callback=groupfinder)
        authz_policy = ACLAuthorizationPolicy()
        self.config.setup_registry(authorization_policy=authz_policy, authentication_policy=authn_policy)


class CatalogTests(CatalogTestCase):
    def test_indexed_on_add(self):
        title_index = self.root.catalog['title']
        title_count = title_index.documentCount()
        meeting = createContent('Meeting')
        meeting.title = 'hello world'
        
        self.root['meeting'] = meeting
        
        self.assertEqual(title_index.documentCount(), title_count + 1)

    def test_unindexed_on_remove(self):
        title_index = self.root.catalog['title']
        title_count = title_index.documentCount()

        meeting = createContent('Meeting')
        meeting.title = 'hello world'
        
        self.root['meeting'] = meeting
        
        self.assertEqual(title_index.documentCount(), title_count + 1)
        
        del self.root['meeting']
        self.assertEqual(title_index.documentCount(), title_count)
        
    def test_reindexed_on_update(self):
        meeting = createContent('Meeting')
        meeting.title = 'hello world'
        self.root['meeting'] = meeting
        
        query = self.query
        self.assertEqual(query("title == 'hello world'")[0], 1)
        
        self.root['meeting'].title = 'me and my little friends'
        #We'll have to kick the subscriber manually
        objectEventNotify(ObjectUpdatedEvent(self.root['meeting']))
        
        self.assertEqual(query("title == 'hello world'")[0], 0)
        self.assertEqual(query("title == 'me and my little friends'")[0], 1)

    def test_update_indexes_when_index_removed(self):
        meeting = createContent('Meeting')
        meeting.title = 'hello world'
        self.root['meeting'] = meeting
        
        catalog = self.root.catalog
        catalog['nonexistent_index'] = catalog['title'] #Nonexistent should be removed
        del catalog['title'] #Removing title index should recreate it
        
        self.failUnless(catalog.get('nonexistent_index'))
        
        from voteit.core.models.catalog import update_indexes
        update_indexes(catalog, reindex=False)
        
        self.failIf(catalog.get('nonexistent_index'))
        self.failUnless(catalog.get('title'))
    
    def test_reindex_indexes(self):
        meeting = createContent('Meeting')
        meeting.title = 'hello world'
        self.root['meeting'] = meeting
        catalog = self.root.catalog
        
        #Catalog should return the meeting on a search
        self.assertEqual(self.query("title == 'hello world'")[0], 1)
        
        #If the meeting title changes, no subscriber will be fired here...
        meeting.title = "Goodbye cruel world"
        #...but when reindexed it should work
        from voteit.core.models.catalog import reindex_indexes
        reindex_indexes(catalog)
        
        self.assertEqual(self.query("title == 'Goodbye cruel world'")[0], 1)

    def test_reindex_object_security(self):
        from voteit.core.models.catalog import reindex_object_security
        self._register_security_policies()
        
        catalog = self.root.catalog
        obj = self._add_mock_meeting()
        reindex_object_security(catalog, obj)

        self.assertEqual(self.query("allowed_to_view in any('role:Admin',) and path == '/meeting'")[0], 1)
        self.assertEqual(self.query("allowed_to_view in any('role:Viewer',) and path == '/meeting'")[0], 1)        


class CatalogIndexTests(CatalogTestCase):
    """ Make sure indexes work as expected. """

    def test_title(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("title == 'Testing catalog'")[0], 1)
    
    def test_sortable_title(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("sortable_title == 'testing catalog'")[0], 1)

    def test_uid(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("uid == 'simple_uid'")[0], 1)

    def test_content_type(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("content_type == 'Meeting'")[0], 1)

    def test_workflow_state(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("workflow_state == 'upcoming'")[0], 1)

    def test_path(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("path == '/meeting'")[0], 1)

    def test_creators(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("creators in any('demo_userid',)")[0], 1)

    def test_created(self):
        """ created actually stores unix-time. Note that it's very
            likely that all objects are added within the same second.
        """
        obj = self._add_mock_meeting()
        from datetime import datetime
        meeting_unix = timegm(obj.created.timetuple())
        
        self.assertEqual(self.query("created == %s and path == '/meeting'" % meeting_unix)[0], 1)
        qy = ("%s < created < %s and path == '/meeting'" % (meeting_unix-1, meeting_unix+1))
        self.assertEqual(self.query(qy)[0], 1)

    def test_allowed_to_view(self):
        self._register_security_policies()
        obj = self._add_mock_meeting()
        
        #Owners are not allowed to view meetings. It's exclusive for Admins / Moderators right now
        self.assertEqual(self.query("allowed_to_view in any('404',) and path == '/meeting'")[0], 0)
        self.assertEqual(self.query("allowed_to_view in any('role:Viewer',) and path == '/meeting'")[0], 1)
        self.assertEqual(self.query("allowed_to_view in any('role:Admin',) and path == '/meeting'")[0], 1)
        self.assertEqual(self.query("allowed_to_view in any('role:Moderator',) and path == '/meeting'")[0], 1)

    def test_view_meeting_userids(self):
        self._register_security_policies()
        #Must add a user to users folder too, otherwise the find_authorized_userids won't accept them as valid
        self.root['users']['demo_userid'] = createContent('User')
        obj = self._add_mock_meeting()
        self.assertEqual(self.search(view_meeting_userids = 'demo_userid')[0], 1)

    def test_searchable_text(self):
        obj = self._add_mock_meeting()
        
        self.assertEqual(self.query("'Testing' in searchable_text")[0], 1)
        self.assertEqual(self.query("'everything works as expected' in searchable_text")[0], 1)
        #FIXME: Not possible to search on "Not", wtf?
        self.assertEqual(self.query("'We are 404' in searchable_text")[0], 0)

    def test_start_time(self):
        obj = self._add_mock_meeting()

        now = utcnow()
        now_unix = timegm(now.timetuple())
        
        #Shouldn't return anything
        self.assertEqual(self.query("start_time == %s and path == '/meeting'" % now_unix)[0], 0)
        qy = ("%s < start_time < %s and path == '/meeting'" % (now_unix-1, now_unix+1))
        self.assertEqual(self.query(qy)[0], 0)
        
        #So let's set it and return stuff
        obj.set_field_value('start_time', now)
        from voteit.core.models.catalog import reindex_indexes
        reindex_indexes(self.root.catalog)
        
        self.assertEqual(self.query("start_time == %s and path == '/meeting'" % now_unix)[0], 1)
        qy = ("%s < start_time < %s and path == '/meeting'" % (now_unix-1, now_unix+1))
        self.assertEqual(self.query(qy)[0], 1)

    def test_end_time(self):
        obj = self._add_mock_meeting()

        now = utcnow()
        now_unix = timegm(now.timetuple())
        
        obj.set_field_value('end_time', now)
        from voteit.core.models.catalog import reindex_indexes
        reindex_indexes(self.root.catalog)
        
        self.assertEqual(self.query("end_time == %s and path == '/meeting'" % now_unix)[0], 1)
        qy = ("%s < end_time < %s and path == '/meeting'" % (now_unix-1, now_unix+1))
        self.assertEqual(self.query(qy)[0], 1)

    def test_unread(self):
        meeting = self._add_mock_meeting()
        self._register_security_policies()
        #Discussion posts are unread aware
        from voteit.core.models.discussion_post import DiscussionPost
        obj = DiscussionPost()
        obj.title = 'Hello'
        meeting['post'] = obj
        obj.mark_all_unread()
        from voteit.core.models.catalog import reindex_indexes
        reindex_indexes(self.root.catalog)
        
        self.assertEqual(self.search(unread='admin')[0], 1)
        
        obj.mark_as_read('admin')
        
        self.assertEqual(self.search(unread='admin')[0], 0)

    def test_like_userids(self):
        meeting = self._add_mock_meeting()
        from voteit.core.models.discussion_post import DiscussionPost
        obj = DiscussionPost()
        obj.title = 'Hello'
        meeting['post'] = obj
        
        self.assertEqual(self.search(like_userids='admin')[0], 0)
        
        #Set like
        from voteit.core.models.interfaces import IUserTags
        user_tags = self.config.registry.getAdapter(obj, IUserTags)
        user_tags.add('like', 'admin')
        
        self.assertEqual(self.search(like_userids='admin')[0], 1)
        
        user_tags.remove('like', 'admin')
        self.assertEqual(self.search(like_userids='admin')[0], 0)

    def test_voted_userids(self):
        meeting = self._add_mock_meeting()
        self._register_security_policies()
        from voteit.core.models.poll import Poll
        from voteit.core.models.vote import Vote
        self.config.scan('voteit.core.subscribers.vote')

        poll = Poll()
        meeting['poll'] = poll

        poll['v1'] = Vote(creators = ['me'])
        poll['v2'] = Vote(creators = ['other'])

        result = self.search(content_type = 'Poll', voted_userids = 'me')
        self.assertEqual(result[0], 1)


class CatalogMetadataTests(CatalogTestCase):
    """ Test metadata creation. This test also covers catalog subscribers.
    """
    
    def test_title(self):
        self._add_mock_meeting()
        result = self.query("title == 'Testing catalog'")
        doc_id = result[1][0] #Layout is something like: (1, set([123]))
        metadata = self.get_metadata(doc_id)
        
        self.assertTrue('title' in metadata)
        self.assertEqual(metadata['title'], 'Testing catalog')
        
    def test_created(self):
        """ created actually stores unix-time. Note that it's very
            likely that all objects are added within the same second.
            The metadata is regular datetime though.
        """
        obj = self._add_mock_meeting()
        result = self.query("title == 'Testing catalog'")
        doc_id = result[1][0]
        metadata = self.get_metadata(doc_id)
        
        self.assertEqual(obj.created, metadata['created'])
        self.assertTrue(isinstance(metadata['created'], datetime))

    def test_path(self):
        obj = self._add_mock_meeting()
        result = self.search(title = 'Testing catalog')
        doc_id = result[1][0]
        metadata = self.get_metadata(doc_id)
        
        self.assertEqual(metadata['path'], '/meeting')

    def test_workflow_state(self):
        obj = self._add_mock_meeting()
        result = self.search(title = 'Testing catalog')
        doc_id = result[1][0]
        metadata = self.get_metadata(doc_id)
        self.assertEqual(metadata['workflow_state'], 'upcoming')

    def test_content_type(self):
        obj = self._add_mock_meeting()
        result = self.search(title = 'Testing catalog')
        doc_id = result[1][0]
        metadata = self.get_metadata(doc_id)
        
        self.assertEqual(metadata['content_type'], 'Meeting')

    def test_uid(self):
        obj = self._add_mock_meeting()
        result = self.search(title = 'Testing catalog')
        doc_id = result[1][0]
        metadata = self.get_metadata(doc_id)
        
        self.assertEqual(metadata['uid'], obj.uid)

    def test_like_userids(self):
        meeting = self._add_mock_meeting()
        from voteit.core.models.discussion_post import DiscussionPost
        obj = DiscussionPost()
        meeting['post'] = obj
        
        def _get_metadata():
            result = self.search(content_type = 'DiscussionPost')
            doc_id = result[1][0]
            return self.get_metadata(doc_id)
        
        self.assertEqual(_get_metadata()['like_userids'], ())

        #Set like
        from voteit.core.models.interfaces import IUserTags
        user_tags = self.config.registry.getAdapter(obj, IUserTags)
        user_tags.add('like', 'admin')

        self.assertEqual(_get_metadata()['like_userids'], ('admin',))
        
        user_tags.remove('like', 'admin')
        self.assertEqual(_get_metadata()['like_userids'], ())

    def test_unread(self):
        meeting = self._add_mock_meeting()
        self._register_security_policies()
        #Discussion posts are unread aware
        from voteit.core.models.discussion_post import DiscussionPost
        obj = DiscussionPost()
        obj.title = 'Hello'
        meeting['post'] = obj
        obj.mark_all_unread()
        from voteit.core.models.catalog import reindex_indexes
        reindex_indexes(self.root.catalog)

        def _get_metadata():
            result = self.search(content_type = 'DiscussionPost')
            doc_id = result[1][0]
            return self.get_metadata(doc_id)
        
        self.assertEqual(_get_metadata()['unread'], frozenset(['admin']) )

    def test_voted_userids(self):
        meeting = self._add_mock_meeting()
        self._register_security_policies()
        from voteit.core.models.poll import Poll
        from voteit.core.models.vote import Vote
        self.config.scan('voteit.core.subscribers.vote')

        poll = Poll()
        meeting['poll'] = poll

        poll['v1'] = Vote(creators = ['me'])
        poll['v2'] = Vote(creators = ['other'])

        result = self.search(content_type = 'Poll')
        doc_id = result[1][0]
        self.assertEqual(self.get_metadata(doc_id)['voted_userids'], frozenset(['me', 'other']) )
