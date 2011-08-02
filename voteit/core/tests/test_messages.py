import unittest

from pyramid import testing
from zope.interface.verify import verifyObject
import transaction

from voteit.core.testing import testing_sql_session


class MessagesTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = testing_sql_session(self.config)
        self.config.include('pyramid_zcml')
        self.config.load_zcml('voteit.core:configure.zcml')        

    def tearDown(self):
        testing.tearDown()
        transaction.abort() #To cancel any commit to the sql db

    def _import_class(self):
        from voteit.core.models.message import Messages
        return Messages

    def _add_mock_data(self, obj):
        data = (
            ('m1', 'test', ('alert', 'social', ), None, None,),
            ('m1', 'test', ('log',), 'm1', None,),
            ('m1', 'test', ('like',), 'p1', 'robin',),
            ('m1', 'test', ('alert',), 'v1', 'robin',),
            ('m1', 'test', ('log',), 'p1', None,),
            ('m1', 'test', ('log',), 'v1', None,),
         )
        for (meetinguid, message, tags, contextuid, userid) in data:
            obj.add(meetinguid, message, tags, contextuid, userid)

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import IMessages
        obj = self._import_class()(self.session)
        self.assertTrue(verifyObject(IMessages, obj))
        
    def test_tag_to_obj(self):
        from voteit.core.models.message import MessageTag
        tags = []
        for tag in ('t1', 't2', 't3'):
            t = MessageTag(tag)
            self.session.add(t)
            tags.append(t)
        
        obj = self._import_class()(self.session)
        for tag in ('t1', 't2', 't3'):
            t = obj.tag_to_obj(tag)
            self.assertTrue(t in tags)

    def test_add(self):
        obj = self._import_class()(self.session)
        meetinguid = 'a1'
        message = 'aa-bb'
        tags = ('log',)
        contextuid = 'a1'
        userid = 'robin'
        obj.add(meetinguid, message, tags, contextuid, userid)

        from voteit.core.models.message import Message
        query = self.session.query(Message).filter_by(userid=userid)

        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.meetinguid, meetinguid)
        self.assertEqual(result_obj.message, message)
        self.assertEqual(result_obj.string_tags, tags)

    def test_retrieve_user_messages(self):
        obj = self._import_class()(self.session)
        self._add_mock_data(obj)

        self.assertEqual(len(obj.retrieve_messages('m1', tags=('like','log',), contextuid='v1')), 1)
        
    def test_mark_read(self):
        obj = self._import_class()(self.session)
        meetinguid = 'a1'
        message = 'aa-bb'
        tags = ('log',)
        contextuid = 'a1'
        userid = 'robin'
        obj.add(meetinguid, message, tags, contextuid, userid)
        
        from voteit.core.models.message import Message
        # to get the id of the message
        msg = self.session.query(Message).filter(Message.userid==userid).first()

        obj.mark_read(msg.id, userid)

        query = self.session.query(Message).filter(Message.id==msg.id).filter(Message.userid==userid)
        self.assertEqual(len(query.all()), 1)
        result_obj = query.all()[0]
        self.assertEqual(result_obj.id, msg.id)
        self.assertEqual(result_obj.userid, userid)
        self.assertEqual(result_obj.unread, False)

    def test_tags_created_on_add(self):
        obj = self._import_class()(self.session)
        self._add_mock_data(obj)
        
        from voteit.core.models.message import Message
        query = self.session.query(Message)

        mock_tags = set()
        for result in query.all():
            mock_tags.update(result.string_tags)
        
        obj.add('m1', 'message', tags=('first_new', 'second_new',))
        
        new_tags = set()
        for result in query.all():
            new_tags.update(result.string_tags)
        
        self.assertNotEqual(mock_tags, new_tags)
        self.assertEqual(new_tags, mock_tags | set(('first_new', 'second_new',)))

    def test_unread_count_in_meeting(self):
        obj = self._import_class()(self.session)
        self._add_mock_data(obj)
        
        self.assertEqual(obj.unreadcount_in_meeting('m1', 'robin'), 2)
        

#FIXME: Test subscribers
