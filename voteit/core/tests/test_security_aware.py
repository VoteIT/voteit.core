import unittest

from pyramid import testing




class SecurityAwareTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        """ Security aware is a mixin class, so we need to add BaseContent too"""
        from voteit.core.models.security_aware import SecurityAware
        from voteit.core.models.base_content import BaseContent
        
        class DummyContent(BaseContent, SecurityAware):
            pass
        
        return DummyContent()

    def _bootstrap_root(self):
        """ Create a default app root"""
        from voteit.core.bootstrap import bootstrap_voteit
        return bootstrap_voteit()

    def test_verify_object(self):
        from zope.interface.verify import verifyObject
        from voteit.core.models.interfaces import ISecurityAware
        obj = self._make_obj()
        self.assertTrue(verifyObject(ISecurityAware, obj))

    def test_get_groups(self):
        obj = self._make_obj()
        self.assertEqual(obj.get_groups('User 404'), ())
        obj.add_groups('tester', ['group:Hipsters'])
        self.assertEqual(obj.get_groups('tester'), ('group:Hipsters',))

    def test_add_groups(self):
        obj = self._make_obj()
        obj.add_groups('tester', ['group:Hipsters'])
        self.assertEqual(obj.get_groups('tester'), ('group:Hipsters',))
        obj.add_groups('tester', ('role:Admin',))
        self.assertEqual(obj.get_groups('tester'), ('group:Hipsters','role:Admin',))

    def test_set_groups(self):
        obj = self._make_obj()
        obj.set_groups('tester', ['group:Hipsters'])
        self.assertEqual(obj.get_groups('tester'), ('group:Hipsters',))
        obj.set_groups('tester', ('role:Admin',))
        self.assertEqual(obj.get_groups('tester'), ('role:Admin',))

    def test_add_bad_group(self):
        obj = self._make_obj()
        self.assertRaises(ValueError, obj.add_groups, 'tester', ['Hipsters'])

    def test_get_security_appstruct(self):
        obj = self._make_obj()
        self.assertEqual(obj.get_security_appstruct(), {'userids_and_groups': []})
        obj.set_groups('robin', ['role:Admin', 'group:Hipsters'])
        self.assertEqual(obj.get_security_appstruct(),
                         {'userids_and_groups': [{'userid': 'robin', 'groups': ('group:Hipsters', 'role:Admin')}]})

    def test_update_from_form(self):
        obj = self._make_obj()
        obj.update_from_form([{'userid': 'robin', 'groups': ('group:DeathCab', 'role:Moderator')}])
        self.assertEqual(obj._groups['robin'], ('group:DeathCab', 'role:Moderator'))

    def test_list_all_groups(self):
        obj = self._make_obj()
        obj.add_groups('tester1', ['group:Hipsters'])
        obj.add_groups('tester2', ['role:Confused', 'group:Hipsters'])
        obj.add_groups('tester3', ['role:Confused', 'group:PeterLicht'])
        self.assertEqual(obj.list_all_groups(), set(('group:Hipsters', 'role:Confused', 'group:PeterLicht')) )