import unittest

from pyramid import testing

from voteit.core.models.interfaces import ISecurityAware


class SecurityAwareTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.security_aware import SecurityAware
        return SecurityAware()

    def test_verify_object(self):
        from zope.interface.verify import verifyObject
        obj = self._make_obj()
        self.assertTrue(verifyObject(ISecurityAware, obj))

    def test_get_groups(self):
        obj = self._make_obj()
        self.assertEqual(obj.get_groups('User 404'), ())
        obj.add_groups('tester', ['group:Hipsters'])
        self.assertEqual(obj.get_groups('tester'), ('group:Hipsters',))

    def test_get_groups_owner_not_inherited(self):
        from voteit.core.security import ROLE_OWNER
        #BaseContent is persistent and security aware
        from voteit.core.models.base_content import BaseContent
        root = BaseContent()
        root.add_groups('tester', [ROLE_OWNER])
        self.assertEqual(root.get_groups('tester'), (ROLE_OWNER,))
        obj = BaseContent()
        obj.add_groups('tester', ['group:Beatles'])
        root['child'] = obj
        #Just to make sure traversal is working :)
        self.assertEqual(root, obj.__parent__)
        #Should not pick up owner role
        self.assertEqual(obj.get_groups('tester'), ('group:Beatles',))

    def test_add_groups(self):
        obj = self._make_obj()
        obj.add_groups('tester', ['group:Hipsters'])
        self.assertEqual(obj.get_groups('tester'), ('group:Hipsters',))
        obj.add_groups('tester', ('role:Admin',))
        self.assertEqual(obj.get_groups('tester'), ('group:Hipsters','role:Admin',))

    def test_get_security(self):
        obj = self._make_obj()
        self.assertEqual(obj.get_security(), ())
        groups_set = set(['role:Admin', 'group:Hipsters'])
        obj.set_groups('robin', groups_set)
        res = obj.get_security()
        self.assertEqual(len(res), 1)
        self.assertEqual(set(res[0]['groups']), groups_set)

    def test_set_security(self):
        obj = self._make_obj()
        groups_set = set(['role:Admin', 'group:Hipsters'])
        value = [{'userid':'robin', 'groups':groups_set},
                 {'userid':'fredrik', 'groups':groups_set}]
        obj.set_security(value)
        res = obj.get_security()
        self.assertEqual(len(res), 2)
        self.assertEqual(set(res[0]['groups']), groups_set)

    def test_set_security_clears_old_value(self):
        obj = self._make_obj()
        groups_set = set(['role:Admin', 'group:Hipsters'])
        value = [{'userid':'robin', 'groups':groups_set},
                 {'userid':'fredrik', 'groups':groups_set}]
        obj.set_security(value)
        value = [{'userid':'robin', 'groups':groups_set}]
        obj.set_security(value)
        res = obj.get_security()
        self.assertEqual(len(res), 1)

    def test_set_groups(self):
        obj = self._make_obj()
        obj.set_groups('tester', ['group:Hipsters'])
        self.assertEqual(obj.get_groups('tester'), ('group:Hipsters',))
        obj.set_groups('tester', ('role:Admin',))
        self.assertEqual(obj.get_groups('tester'), ('role:Admin',))

    def test_set_groups_notifies(self):
        from voteit.core.interfaces import IObjectUpdatedEvent
        L = []
        def subscriber(obj, event):
            L.append(event)
        self.config.add_subscriber(subscriber, iface=[ISecurityAware, IObjectUpdatedEvent])
        self.config.commit()
        obj = self._make_obj()
        obj.set_groups('dummy', ['role:Speaker'], event = True)
        self.assertEqual(len(L), 1)
        self.failUnless(IObjectUpdatedEvent.providedBy(L[0]))

    def test_set_groups_with_dependent_group(self):
        from voteit.core import security
        obj = self._make_obj()
        obj.set_groups('tester', [security.ROLE_PROPOSE])
        res_set = set(obj.get_groups('tester'))
        self.assertEqual(res_set, set([security.ROLE_PROPOSE, security.ROLE_VIEWER]))

    def test_set_groups_with_no_groups_specified_deletes_setting(self):
        obj = self._make_obj()
        obj.set_groups('tester', ['role:HelloWorld'])
        self.failUnless('tester' in obj._groups)
        obj.set_groups('tester', [])
        self.failIf('tester' in obj._groups)

    def test_add_bad_group(self):
        obj = self._make_obj()
        self.assertRaises(ValueError, obj.add_groups, 'tester', ['Hipsters'])

    def test_del_group(self):
        obj = self._make_obj()
        obj.set_groups('tester', ['role:HelloWorld', 'role:Other'])
        obj.del_groups('tester', ['role:HelloWorld'])
        self.failIf('role:HelloWorld' in obj.get_groups('tester'))

    def test_list_all_groups(self):
        obj = self._make_obj()
        obj.add_groups('tester1', ['group:Hipsters'])
        obj.add_groups('tester2', ['role:Confused', 'group:Hipsters'])
        obj.add_groups('tester3', ['role:Confused', 'group:PeterLicht'])
        self.assertEqual(obj.list_all_groups(), set(('group:Hipsters', 'role:Confused', 'group:PeterLicht')) )
