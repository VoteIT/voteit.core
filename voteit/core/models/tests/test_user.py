import unittest

from arche.testing import barebone_fixture
from zope.interface.verify import verifyObject
from pyramid import testing
from pyramid.security import principals_allowed_by_permission

from voteit.core import security
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
        root = barebone_fixture()
        request = testing.DummyRequest()
        request.root = root
        root['users']['jane'] = obj = self._make_obj()
        obj.set_field_value('email', 'hello@world.com')
        self.assertEqual(
            '<img src="https://secure.gravatar.com/avatar/4b3cdf9adfc6258a102ab90eb64565ea?s=45&d=robohash" height="45" width="45" class="profile-pic" />',
             obj.get_image_tag(size=45, request=request)
         )

    def test_get_image_tag_no_plugin(self):
        self.config.registry.settings['voteit.default_profile_picture'] = 'some_pic.png'
        obj = self._make_obj()
        self.assertEqual(obj.get_image_tag(size=45),
                         '<img src="some_pic.png" height="45" width="45" class="profile-pic" />')


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
