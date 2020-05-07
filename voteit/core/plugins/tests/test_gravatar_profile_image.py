import unittest

from pyramid import testing
from pyramid.traversal import find_root
from zope.interface.verify import verifyObject


class GravatarProfileImageUnitTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.plugins.gravatar_profile_image import (
            GravatarProfileImagePlugin,
        )
        from voteit.core.models.user import User
        from voteit.core.models.site import SiteRoot

        root = SiteRoot()
        root["user"] = User(email="hello@world.com")
        return GravatarProfileImagePlugin(root["user"])

    def test_verify_implementation(self):
        from voteit.core.models.interfaces import IProfileImage

        obj = self._make_obj()
        self.assertTrue(verifyObject(IProfileImage, obj))

    def test_url_method(self):
        obj = self._make_obj()
        request = testing.DummyRequest()
        request.root = find_root(obj.context)
        url = obj.url(45, request)
        self.assertEqual(
            "https://secure.gravatar.com/avatar/4b3cdf9adfc6258a102ab90eb64565ea?s=45&d=robohash",
            url,
        )

    def test_is_valid(self):
        obj = self._make_obj()
        self.assertTrue(obj.is_valid_for_user())
