import unittest

from pyramid import testing
from zope.interface.verify import verifyObject


class DiscussionTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _make_obj(self):
        from voteit.core.models.discussion_post import DiscussionPost        
        return DiscussionPost()

    def test_verify_obj_implementation(self):
        from voteit.core.models.interfaces import IDiscussionPost
        obj = self._make_obj()
        self.assertTrue(verifyObject(IDiscussionPost, obj))
