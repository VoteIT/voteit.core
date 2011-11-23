import unittest

from pyramid import testing
from pyramid.url import resource_url
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.core.models.interfaces import IDiscussionPost


class DiscussionTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.models.discussion_post import DiscussionPost
        return DiscussionPost

    def test_verify_class(self):
        self.assertTrue(verifyClass(IDiscussionPost, self._cut))

    def test_verify_obj(self):
        self.assertTrue(verifyObject(IDiscussionPost, self._cut()))

    def test_newline_to_br_enabled(self):
        obj = self._cut()
        obj.set_field_value('text', 'test\ntest')
        self.assertEqual(unicode(obj.get_field_value('text')), unicode('test<br /> test'))

    def test_autolinking_enabled(self):
        obj = self._cut()
        obj.set_field_value('text', 'www.betahaus.net')
        self.assertEqual(unicode(obj.get_field_value('text')), unicode('<a href="http://www.betahaus.net">www.betahaus.net</a>'))

    def test_title_and_text_linked(self):
        obj = self._cut()
        obj.set_field_value('title', "Hello")
        self.assertEqual(obj.get_field_value('text'), "Hello")

    def test_nl2br_several_runs_should_not_add_more_brs(self):
        obj = self._cut()
        obj.title = "Hello\nthere"
        res = obj.get_field_value('title')
        obj.title = res
        result = obj.get_field_value('title')
        self.assertEqual(result.count('<br />'), 1)

    #FIXME: We need proper permission tests here
