import unittest
from datetime import timedelta
from datetime import datetime

from pyramid import testing
from zope.interface.verify import verifyObject
from zope.component.event import objectEventNotify
from pyramid_mailer import get_mailer
from repoze.folder.events import ObjectAddedEvent
from pyramid.url import resource_url

from voteit.core.models.date_time_util import utcnow
from voteit.core.exceptions import TokenValidationError


class UserTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.user import User
        return User()

    def test_verify_interface(self):
        from voteit.core.models.interfaces import IUser
        obj = self._make_obj()
        self.assertTrue(verifyObject(IUser, obj))
    
    def test_userid(self):
        from voteit.core.models.users import Users
        users = Users()
        obj = self._make_obj()
        users['my_userid'] = obj
        
        self.assertEqual(obj.userid, u'my_userid')
        self.assertEqual(obj.userid, obj.__name__) #Convention
        
    def test_get_and_set_password(self):
        self.config.scan('betahaus.pyracont.fields.password')
        pw = 'very_secret'
        
        obj = self._make_obj()
        field = obj.get_custom_field('password')
        hashed = field.hash_method(pw)
        
        obj.set_password(pw)
        self.assertEqual(obj.get_password(), hashed)
    
    def test_empty_password(self):
        self.config.scan('betahaus.pyracont.fields.password')
        obj = self._make_obj()
        self.assertEqual(obj.get_password(), None)    

    def test_new_request_password_token(self):
        self.config.scan('voteit.core.models.user')
        obj = self._make_obj()
        request = testing.DummyRequest()
        self.config.include('pyramid_mailer.testing')
        obj.new_request_password_token(request)
        self.failUnless(obj.__token__())
    
    def test_new_request_password_token_mailed(self):
        self.config.scan('voteit.core.models.user')
        obj = self._make_obj()
        request = testing.DummyRequest()
        self.config.include('pyramid_mailer.testing')
        
        obj.new_request_password_token(request)

        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        
        msg = mailer.outbox[0]
        
        self.failUnless(obj.__token__() in msg.body)
    
    def test_blank_email_hash_generation(self):
        obj = self._make_obj()
        self.assertEqual(obj.get_image_tag(), '<img src="http://www.gravatar.com/avatar/?d=mm&s=40" height="40" width="40" class="profile-pic" />')

    def test_email_hash_generation_subscriber(self):
        self.config.scan('voteit.core.subscribers.user')
        
        obj = self._make_obj()
        obj.set_field_value('email', 'hello@world.com')
        objectEventNotify(ObjectAddedEvent(obj, None, 'dummy'))
        
        self.assertEqual(obj.get_field_value('email_hash'),
                         '4b3cdf9adfc6258a102ab90eb64565ea')

    def test_email_hash_method(self):
        obj = self._make_obj()
        obj.set_field_value('email', 'hello@world.com')
        obj.generate_email_hash()
        
        self.assertEqual(obj.get_field_value('email_hash'),
                         '4b3cdf9adfc6258a102ab90eb64565ea')

    def test_get_image_tag(self):
        obj = self._make_obj()
        obj.set_field_value('email', 'hello@world.com')
        obj.generate_email_hash()
        
        self.assertEqual(obj.get_image_tag(size=45),
                         '<img src="http://www.gravatar.com/avatar/4b3cdf9adfc6258a102ab90eb64565ea?d=mm&s=45" height="45" width="45" class="profile-pic" />')
                         
    def test_mentioned_email(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        self.config.include('pyramid_mailer.testing')
        self.config.scan('voteit.core.models.site')
        self.config.scan('voteit.core.models.user')
        self.config.scan('voteit.core.models.users')
        self.config.scan('voteit.core.subscribers.transform_text')
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.catalog')
        self.config.scan('betahaus.pyracont.fields.password')

        from voteit.core.bootstrap import bootstrap_voteit
        self.root = bootstrap_voteit(echo=False)
        self.root.users['admin'].set_field_value('email', 'admin@voteit.se')

        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        self.root['meeting'] = meeting
        
        from voteit.core.models.agenda_item import AgendaItem
        agenda_item = AgendaItem()
        meeting['agenda_item'] = agenda_item

        from voteit.core.models.discussion_post import DiscussionPost
        discussion_post = DiscussionPost()
        discussion_post.set_field_value('text', '@admin')
        agenda_item['discussion_post'] = discussion_post

        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        
        msg = mailer.outbox[0]
        self.failUnless(resource_url(discussion_post, request) in msg.html)


class RequestPasswordTokenTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _make_obj(self):
        from voteit.core.models.user import RequestPasswordToken
        return RequestPasswordToken()

    def test_initial_values(self):
        obj = self._make_obj()
        self.assertEqual(obj.created + timedelta(days=3), obj.expires)

    def test_call_returns_token(self):
        obj = self._make_obj()
        self.assertEqual(obj(), obj.token)
        self.assertEqual(len(obj()), 30)
    
    def test_validate_works(self):
        obj = self._make_obj()
        obj.token = 'dummy'
        obj.validate('dummy')
    
    def test_validate_expired(self):
        obj = self._make_obj()
        obj.token = 'dummy'
        obj.expires = utcnow() - timedelta(days=1)
        self.assertRaises(TokenValidationError, obj.validate, 'dummy')

    def test_validate_wrong_token(self):
        obj = self._make_obj()
        obj.token = 'dummy'
        self.assertRaises(TokenValidationError, obj.validate, 'wrong')
