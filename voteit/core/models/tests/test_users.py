import unittest

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from pyramid.security import principals_allowed_by_permission

from voteit.core import security
from voteit.core.testing_helpers import register_security_policies
from voteit.core.models.interfaces import IUsers


admin = set([security.ROLE_ADMIN])


class UsersTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.users import Users
        return Users

    def test_verify_class(self):
        self.assertTrue(verifyClass(IUsers, self._cut))
        
    def test_verify_obj(self):
        self.assertTrue(verifyObject(IUsers, self._cut()))

    def test_get_user_by_email(self):
        obj = self._cut()
        from voteit.core.models.user import User
        obj['user'] = User(email = 'hello@world.org', first_name = 'Anders')
        res = obj.get_user_by_email('hello@world.org')
        self.assertEqual(res.get_field_value('first_name'), 'Anders')

    def test_add_lowercase(self):
        obj = self._cut()
        from voteit.core.models.user import User
        user = User(email = 'hello@world.org', first_name = 'Anders')
        obj['dummy'] = user
        self.assertIn(user, obj.values())
        
    def test_add_uppercase(self):
        obj = self._cut()
        from voteit.core.models.user import User
        user = User(email = 'hello@world.org', first_name = 'Anders')
        self.assertRaises(ValueError, obj.add, 'Dummy', user)

class UsersPermissionTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        register_security_policies(self.config)
        
    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.users import Users
        return Users

    def test_view(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.VIEW), admin)

    def test_edit(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.EDIT), admin)

    def test_delete(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.DELETE), set())

    def test_manage_server(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.MANAGE_SERVER), admin)

    def test_add_user(self):
        obj = self._cut()
        self.assertEqual(principals_allowed_by_permission(obj, security.ADD_USER), admin)
