import unittest

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated
from pyramid.security import Everyone
from zope.interface.verify import verifyObject

from voteit.core import security


admin = set([security.ROLE_ADMIN])
meeting_creator = set([security.ROLE_MEETING_CREATOR])
authenticated = set([Authenticated])
everyone = set([Everyone])


class SiteRootTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.site import SiteRoot
        return SiteRoot()

    def test_verify_interface(self):
        from voteit.core.models.interfaces import IBaseContent
        obj = self._make_obj()
        self.assertTrue(verifyObject(IBaseContent, obj))


class SiteRootPermissionTests(unittest.TestCase):
    """ Check permissions. """

    def setUp(self):
        self.config = testing.setUp()
        policy = ACLAuthorizationPolicy()
        self.pap = policy.principals_allowed_by_permission

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.site import SiteRoot
        return SiteRoot

    def test_add_meeting_perm(self):
        obj = self._cut()
        self.assertEqual(self.pap(obj, security.ADD_MEETING), admin | meeting_creator)

    def test_view(self):
        obj = self._cut()
        self.assertEqual(self.pap(obj, security.VIEW), admin | everyone)
