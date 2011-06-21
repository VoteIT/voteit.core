import unittest

from pyramid import testing
import transaction
from zope.interface.verify import verifyObject
from voteit.core.testing import testing_sql_session


class LogsTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')
        self.session = testing_sql_session(self.config)

    def tearDown(self):
        testing.tearDown()
        transaction.abort() #To cancel any commit to the sql db

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

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import ILogs
        obj = self._import_class()(self.session)
        self.assertTrue(verifyObject(ILogs, obj))

    def test_tag(self):
        from voteit.core.models.log import LogTag
        query = self.session.query(LogTag)
        self.assertEqual(len(query.all()), 5)
        self.assertEqual(len(query.filter(LogTag.tag=='added').all()), 1)
        
    def test_log(self):
        meetinguid = 'm1'
        message = 'lorem ipsum'
        tags = ('added', 'proposal to poll')
        userid = 'robin'
        primaryuid = 'v1'
        secondaryuid = 'p1'

        from voteit.core.models.log import LogTag
        _tags = []
        for tag in tags:
            _tag = self.session.query(LogTag).filter_by(tag=tag).one()
            _tags.append(_tag)
            
            
        from voteit.core.models.log import Log
        log = Log(meetinguid, message, _tags, userid, primaryuid, secondaryuid)
        self.session.add(log)
        
        query = self.session.query(Log)
        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.meetinguid, meetinguid)
        self.assertEqual(result_obj.message, message)
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.primaryuid, primaryuid)
        self.assertEqual(result_obj.secondaryuid, secondaryuid)
        self.assertEqual(len(result_obj.tags), 2)
    
    def test_add(self):        
        obj = self._import_class()(self.session)
        meetinguid = 'a1'
        message = 'aa-bb'
        tags = ('added', 'proposal to poll')
        userid = 'robin'
        primaryuid = 'v1'
        secondaryuid = 'p1'
        obj.add(meetinguid, message, tags, userid, primaryuid, secondaryuid)

        from voteit.core.models.log import Log
        query = self.session.query(Log)

        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.meetinguid, meetinguid)
        self.assertEqual(result_obj.message, message)
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.primaryuid, primaryuid)
        self.assertEqual(result_obj.secondaryuid, secondaryuid)
        self.assertEqual(len(result_obj.tags), 2)

    def test_retrieve_entries(self):        
        obj = self._import_class()(self.session)
        self._add_mock_data(obj)

        self.assertEqual(len(obj.retrieve_entries('m1', tag='added')), 2)

    def test_meeting_added_subscriber_adds_to_log(self):
        #Add subscribers
        self.config.scan('voteit.core.subscribers.log')

        from voteit.core.models.site import SiteRoot
        root = SiteRoot()
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting
        
        logs = self._import_class()(self.session)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='added', primaryuid=meeting.uid)), 1)
        
    def test_added_subscriber_adds_to_log(self):
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
        
        logs = self._import_class()(self.session)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='added')), 4)
        
    def test_deleted_subscriber_adds_to_log(self):        
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
        
        logs = self._import_class()(self.session)
        self.assertEqual(len(logs.retrieve_entries(meeting_uid, tag='deleted')), 4)
        
    def test_state_changed_subscriber_adds_to_log(self):
        #Add subscribers
        self.config.scan('voteit.core.subscribers.log')
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        
        from voteit.core.models.agenda_item import AgendaItem
        ai = AgendaItem()
        meeting['a1'] = ai

        request = testing.DummyRequest()
        ai.set_workflow_state(request, 'inactive')
        
        logs = self._import_class()(self.session)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='state changed')), 1)
        
    def test_proposal_to_poll_subscriber_adds_to_log(self):
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
        
        logs = self._import_class()(self.session)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='added')), 4)

        logs = self._import_class()(self.session)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='proposal to poll')), 2)
        
    def test_updated_subscriber_adds_to_log(self):
        #Add subscribers
        self.config.scan('voteit.core.subscribers.log')
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()

        from zope.component.event import objectEventNotify
        from voteit.core.events import ObjectUpdatedEvent
        objectEventNotify(ObjectUpdatedEvent(meeting))

        logs = self._import_class()(self.session)
        self.assertEqual(len(logs.retrieve_entries(meeting.uid, tag='updated')), 1)
