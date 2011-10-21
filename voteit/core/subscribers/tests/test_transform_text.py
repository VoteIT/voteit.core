from unittest import TestCase

from repoze.folder.events import ObjectAddedEvent
from pyramid import testing
from zope.component.event import objectEventNotify

from voteit.core.testing_helpers import bootstrap_and_fixture


class TransformTextTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _fixture(self):
        return bootstrap_and_fixture(self.config)

    @property
    def _meeting(self):
        """ Has metadata enabled """
        from voteit.core.models.meeting import Meeting
        return Meeting
        
    @property
    def _ai(self):
        """ Has metadata enabled """
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem

    def _make_disc(self):
        root = self._fixture()
        
        meeting = self._meeting()
        root['meeting'] = meeting
        
        ai = self._ai()
        meeting['ai'] = ai

        from voteit.core.models.discussion_post import DiscussionPost
        disc = DiscussionPost()
        ai['disc'] = disc
        
        return disc
        
    def _make_prop(self):
        root = self._fixture()
        
        meeting = self._meeting()
        root['meeting'] = meeting
        
        ai = self._ai()
        meeting['ai'] = ai

        from voteit.core.models.proposal import Proposal
        prop = Proposal()
        ai['prop'] = prop
        
        return prop

    def test_discussion_post_newline_to_br(self):
        self.config.scan('voteit.core.subscribers.transform_text')
    
        disc = self._make_disc()
        disc.set_field_value('text', 'test\ntest')
        objectEventNotify(ObjectAddedEvent(disc, None, 'dummy'))

        from webhelpers.html.converters import nl2br
        self.assertEqual(disc.get_field_value('text'), unicode(nl2br('test\ntest')))

    def test_proposal_newline_to_br(self):
        self.config.scan('voteit.core.subscribers.transform_text')
    
        prop = self._make_prop()
        prop.set_field_value('title', 'test\ntest')
        objectEventNotify(ObjectAddedEvent(prop, None, 'dummy'))

        from webhelpers.html.converters import nl2br
        self.assertEqual(prop.get_field_value('title'), unicode(nl2br('test\ntest')))

    def test_discussion_post_urls_to_links(self):
        self.config.scan('voteit.core.subscribers.transform_text')
    
        disc = self._make_disc()
        disc.set_field_value('text', 'http://www.test.com')
        objectEventNotify(ObjectAddedEvent(disc, None, 'dummy'))

        from webhelpers.html.tools import auto_link
        self.assertEqual(disc.get_field_value('text'), unicode(auto_link('http://www.test.com')))

    def test_proposal_urls_to_links(self):
        self.config.scan('voteit.core.subscribers.transform_text')
    
        prop = self._make_prop()
        prop.set_field_value('title', 'http://www.test.com')
        objectEventNotify(ObjectAddedEvent(prop, None, 'dummy'))

        from webhelpers.html.tools import auto_link
        self.assertEqual(prop.get_field_value('title'), unicode(auto_link('http://www.test.com')))

    def test_discussion_at_userid_link(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        self.config.scan('voteit.core.subscribers.transform_text')
    
        disc = self._make_disc()
        disc.set_field_value('text', '@admin')
        objectEventNotify(ObjectAddedEvent(disc, None, 'dummy'))

        from ..transform_text import at_userid_link
        self.assertEqual(disc.get_field_value('text'), unicode(at_userid_link('@admin', disc)))

    def test_proposal_at_userid_link(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        self.config.scan('voteit.core.subscribers.transform_text')
    
        prop = self._make_prop()
        prop.set_field_value('title', '@admin')
        objectEventNotify(ObjectAddedEvent(prop, None, 'dummy'))

        from ..transform_text import at_userid_link
        self.assertEqual(prop.get_field_value('title'), unicode(at_userid_link('@admin', prop)))
