import unittest
from datetime import timedelta

from zope.interface.verify import verifyObject
from pyramid import testing
from pyramid_mailer import get_mailer
from pyramid.url import resource_url
from pyramid.security import principals_allowed_by_permission

from voteit.core import security
from voteit.core.models.date_time_util import utcnow
from voteit.core.exceptions import TokenValidationError
from voteit.core.testing_helpers import register_security_policies
from voteit.core.models.interfaces import IProfileImage
from voteit.core.models.interfaces import IUser


admin = set([security.ROLE_ADMIN])
owner = set([security.ROLE_OWNER])


class UserTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.user import User
        return User()

    def _register_mock_image_plugin(self):
        self.config.registry.registerAdapter(_MockImagePlugin, (IUser,), IProfileImage, _MockImagePlugin.name)

    def test_verify_interface(self):
        obj = self._make_obj()
        self.assertTrue(verifyObject(IUser, obj))
    
    def test_userid(self):
        from voteit.core.models.users import Users
        users = Users()
        obj = self._make_obj()
        users['my_userid'] = obj
        
        self.assertEqual(obj.userid, u'my_userid')
        self.assertEqual(obj.userid, obj.__name__) #Convention

    def test_title_is_fullname(self):
        obj = self._make_obj()
        self.assertEqual(obj.title, '')
        obj.set_field_value('first_name', 'John')
        self.assertEqual(obj.title, 'John')
        obj.set_field_value('last_name', 'Doe')
        self.assertEqual(obj.title, 'John Doe')

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
        self.config.include('pyramid_chameleon')
        self.config.scan('voteit.core.models.user')
        self.config.scan('voteit.core.views.components.email')
        obj = self._make_obj()
        request = testing.DummyRequest()
        self.config.include('pyramid_mailer.testing')
        obj.new_request_password_token(request)
        self.failUnless(obj.__token__())
    
    def test_new_request_password_token_mailed(self):
        self.config.include('pyramid_chameleon')
        self.config.scan('voteit.core.models.user')
        self.config.scan('voteit.core.views.components.email')
        obj = self._make_obj()
        request = testing.DummyRequest()
        self.config.include('pyramid_mailer.testing')
        obj.new_request_password_token(request)
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        msg = mailer.outbox[0]
        self.failUnless(obj.__token__() in msg.html)

    def test_get_image_plugin(self):
        self._register_mock_image_plugin()
        obj = self._make_obj()
        request = testing.DummyRequest()
        obj.set_field_value('profile_image_plugin', 'mock_image_plugin')
        self.assertIsInstance(obj.get_image_plugin(request), _MockImagePlugin)

    def test_get_image_plugin_broken_plugin(self):
        obj = self._make_obj()
        request = testing.DummyRequest()
        obj.set_field_value('profile_image_plugin', 'i_dont_exist')
        self.assertEqual(obj.get_image_plugin(request), None)

    def test_get_image_tag(self):
        self.config.include('voteit.core.plugins.gravatar_profile_image')
        obj = self._make_obj()
        obj.set_field_value('email', 'hello@world.com')
        self.assertEqual(obj.get_image_tag(size=45),
                         '<img src="https://secure.gravatar.com/avatar/4b3cdf9adfc6258a102ab90eb64565ea?s=45&d=mm" height="45" width="45" class="profile-pic" />')

    def test_get_image_tag_no_plugin(self):
        self.config.registry.settings['voteit.default_profile_picture'] = 'some_pic.png'
        obj = self._make_obj()
        self.assertEqual(obj.get_image_tag(size=45),
                         '<img src="some_pic.png" height="45" width="45" class="profile-pic" />')

    def test_mentioned_email(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        self.config.include('pyramid_mailer.testing')
        self.config.scan('voteit.core.models.site')
        self.config.scan('voteit.core.models.agenda_template')
        self.config.scan('voteit.core.models.agenda_templates')
        self.config.scan('voteit.core.models.user')
        self.config.scan('voteit.core.models.users')
        self.config.scan('voteit.core.subscribers.mention')
        self.config.include('voteit.core.models.user_tags')
        self.config.include('voteit.core.models.catalog')
        self.config.scan('betahaus.pyracont.fields.password')

        from voteit.core.bootstrap import bootstrap_voteit
        root = bootstrap_voteit(echo=False)
        root.users['admin'].set_field_value('email', 'admin@voteit.se')

        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        root['meeting'] = meeting
        
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


class UserPermissionTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        register_security_policies(self.config)
        
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.user import User
        return User

    def test_view(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.VIEW), admin | owner)

    def test_edit(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.EDIT), admin | owner)

    def test_delete(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.DELETE), admin)

    def test_manage_server(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.MANAGE_SERVER), admin)

    def test_change_password(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.CHANGE_PASSWORD), admin | owner)


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


class _MockImagePlugin(object):
    name = "mock_image_plugin"
    title = "Mock"
    description = "for testing"

    def __init__(self, context):
        self.context = context

    def url(self, size, request):
        "http://www.voteit.se?size=%s" % size

    def is_valid_for_user(self):
        return True
