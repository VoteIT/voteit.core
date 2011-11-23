from unittest import TestCase

from pyramid import testing
from repoze.folder.events import ObjectAddedEvent
from zope.component.event import objectEventNotify


class MentionSubscriberTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.subscribers.mention import transform_at_links
        return transform_at_links

    #FIXME: Write tests
