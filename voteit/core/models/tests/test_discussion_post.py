import unittest

from pyramid import testing
from pyramid.url import resource_url
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
        
    def test_transform_text_subscriber(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)

        self.config.scan('voteit.core.models.site')
        self.config.scan('voteit.core.models.user')
        self.config.scan('voteit.core.models.users')
        self.config.scan('voteit.core.subscribers.transform_text')
        self.config.include('voteit.core.models.catalog')        
        self.config.include('voteit.core.models.user_tags')
        self.config.scan('betahaus.pyracont.fields.password')

        from voteit.core.bootstrap import bootstrap_voteit
        self.root = bootstrap_voteit(echo=False)
        
        from voteit.core.models.meeting import Meeting
        meeting = Meeting()
        self.root['m1'] = meeting
        
        obj = self._make_obj()
        obj.set_field_value('text', 'test\ntest')
        meeting['p1'] = obj
        self.assertEqual(obj.get_field_value('text'), 'test<br />\ntest')

        obj = self._make_obj()
        obj.set_field_value('text', 'http://www.voteit.se')
        meeting['p2'] = obj
        self.assertEqual(obj.get_field_value('text'), '<a href="http://www.voteit.se">http://www.voteit.se</a>')
        
        obj = self._make_obj()
        obj.set_field_value('text', '@admin')
        meeting['p3'] = obj

        from webhelpers.html import HTML
        a_options = dict()
        a_options['href'] = "%s_userinfo?userid=%s" % (resource_url(meeting, request), 'admin')
        a_options['title'] = self.root.users['admin'].title
        a_options['class'] = "inlineinfo"
        text = HTML.a('@admin', **a_options)

        self.assertEqual(obj.get_field_value('text'), text)

    #FIXME: We need proper permission tests here
