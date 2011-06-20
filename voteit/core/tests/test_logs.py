import unittest
import os

from pyramid import testing
from zope.interface.verify import verifyObject

from voteit.core.app import init_sql_database
from voteit.core.testing import DummyRequestWithVoteIT


class LogsTests(unittest.TestCase):

    def setUp(self):
        self.request = DummyRequestWithVoteIT()
        self.config = testing.setUp(request=self.request)

        settings = {}
        self.dbfile = '_temp_testing_sqlite.db'
        settings['sqlite_file'] = 'sqlite:///%s' % self.dbfile
        init_sql_database(settings)
        self.request.registry.settings = settings
        
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')

    def tearDown(self):
        testing.tearDown()
        #Is this really smart? Pythons tempfile module created lot's of crap that wasn't cleaned up
        os.unlink(self.dbfile)

    def _import_class(self):
        from voteit.core.models.log import Logs
        return Logs

    def _add_mock_data(self, obj):
        data = (
            ('m1', 'test', ('added',), 'fredrik', None, None,),
            ('m1', 'test', ('updated',), 'anders', None, None,),
            ('m1', 'test', ('deleted',), 'robin', None, None,),
            ('m1', 'test', ('state changed',), 'robin', 'v1', None,),
            ('m1', 'test', ('deleted',), 'hanna', 'p1', None,),
            ('m1', 'test', ('added','proposal to poll',), 'hanna', 'v1', 'p1',),
         )
        for (meetinguid, message, tag, userid, primaryuid, secondaryuid) in data:
            obj.add(meetinguid, message, tag, userid, primaryuid, secondaryuid)

    def _init_tags(self):
        from voteit.core.models.log import Tag
        session = self.request.sql_session
        tags = ('added', 'updated', 'deleted', 'state changed', 'proposal to poll')
        for tag in tags:
            _tag = Tag(tag)
            session.add(_tag)

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import ILogs
        obj = self._import_class()(self.request)
        self.assertTrue(verifyObject(ILogs, obj))

    def test_tag(self):
        self._init_tags()
        
        from voteit.core.models.log import Tag
        session = self.request.sql_session
        query = session.query(Tag)
        self.assertEqual(len(query.all()), 5)
        self.assertEqual(len(query.filter(Tag.tag=='added').all()), 1)
        
    def test_log(self):
        meetinguid = 'm1'
        message = 'lorem ipsum'
        tags = ('added', 'proposal to poll')
        userid = 'robin'
        primaryuid = 'v1'
        secondaryuid = 'p1'

        self._init_tags()
        session = self.request.sql_session

        from voteit.core.models.log import Tag
        _tags = []
        for tag in tags:
            _tag = session.query(Tag).filter_by(tag=tag).one()
            _tags.append(_tag)
            
            
        from voteit.core.models.log import Log
        log = Log(meetinguid, message, _tags, userid, primaryuid, secondaryuid)
        session.add(log)
        
        query = session.query(Log)
        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.meetinguid, meetinguid)
        self.assertEqual(result_obj.message, message)
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.primaryuid, primaryuid)
        self.assertEqual(result_obj.secondaryuid, secondaryuid)
        self.assertEqual(len(result_obj.tags), 2)
    
    def test_add(self):
        self._init_tags()
        
        obj = self._import_class()(self.request)
        meetinguid = 'a1'
        message = 'aa-bb'
        tags = ('added', 'proposal to poll')
        userid = 'robin'
        primaryuid = 'v1'
        secondaryuid = 'p1'
        obj.add(meetinguid, message, tags, userid, primaryuid, secondaryuid)

        from voteit.core.models.log import Log
        session = self.request.sql_session
        query = session.query(Log)

        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.meetinguid, meetinguid)
        self.assertEqual(result_obj.message, message)
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.primaryuid, primaryuid)
        self.assertEqual(result_obj.secondaryuid, secondaryuid)
        self.assertEqual(len(result_obj.tags), 2)

    def test_retrieve_entries(self):
        self._init_tags()
        
        obj = self._import_class()(self.request)
        self._add_mock_data(obj)

        self.assertEqual(len(obj.retrieve_entries('m1', tag='added')), 2)

    def test_meeting_added_subscriber_adds_to_log(self):
        self._init_tags()

        #Add subscribers
        self.config.scan('voteit.core.subscribers.log')

        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting
        
        logs = self._import_class()(self.request)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='added', primaryuid=meeting.uid)), 1)
        
    def test_added_subscriber_adds_to_log(self):
        self._init_tags()

        #Add subscribers
        self.config.scan('voteit.core.subscribers.log')
        
        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting
        
        from voteit.core.models.agenda_item import AgendaItem
        ai = AgendaItem()
        meeting['a1'] = ai
        
        from voteit.core.models.proposal import Proposal
        po = Proposal()
        ai['p1'] = po
        
        from voteit.core.models.proposal import Proposal
        vo = Proposal()
        ai['v1'] = vo
        
        logs = self._import_class()(self.request)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='added')), 4)
        
    def test_deleted_subscriber_adds_to_log(self):
        self._init_tags()
        
        #Add subscribers
        self.config.scan('voteit.core.subscribers.log')

        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting
        meeting_uid = meeting.uid # Because we delete meeting later and we need to have the uid to check the database
        
        from voteit.core.models.agenda_item import AgendaItem
        ai = AgendaItem()
        meeting['a1'] = ai
        
        from voteit.core.models.proposal import Proposal
        po = Proposal()
        ai['p1'] = po
        
        from voteit.core.models.poll import Poll
        vo = Poll()
        ai['v1'] = vo
        
        del ai['v1']
        del ai['p1']
        del meeting['a1']
        del root['meeting']
        
        logs = self._import_class()(self.request)
        self.assertEqual(len(logs.retrieve_entries(meeting_uid, tag='deleted')), 4)
        
    def test_state_changed_subscriber_adds_to_log(self):
        self._init_tags()
        
        #Add subscribers
        self.config.scan('voteit.core.subscribers.log')
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        
        from voteit.core.models.agenda_item import AgendaItem
        ai = AgendaItem()
        meeting['a1'] = ai

        ai.set_workflow_state(self.request, 'inactive')
        
        logs = self._import_class()(self.request)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='state changed')), 1)
        
    def test_proposal_to_poll_subscriber_adds_to_log(self):
        self._init_tags()
        
        #Add subscribers
        self.config.scan('voteit.core.subscribers.log')
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
    
        from voteit.core.models.agenda_item import AgendaItem
        ai = AgendaItem()
        meeting['a1'] = ai
        
        from voteit.core.models.proposal import Proposal
        p1 = Proposal()
        ai['p1'] = p1
        
        p2 = Proposal()
        ai['p2'] = p2
        
        from voteit.core.models.poll import Poll
        vo = Poll()
        vo.proposal_uids = (p1.uid, p2.uid)
        ai['v1'] = vo
        
        logs = self._import_class()(self.request)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='added')), 4)

        logs = self._import_class()(self.request)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='proposal to poll')), 2)
        
    def test_updated_subscriber_adds_to_log(self):
        self._init_tags()
        
        #Add subscribers
        self.config.scan('voteit.core.subscribers.log')
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()

        from zope.component.event import objectEventNotify
        from voteit.core.events import ObjectUpdatedEvent
        objectEventNotify(ObjectUpdatedEvent(meeting))

        logs = self._import_class()(self.request)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='updated')), 1)
