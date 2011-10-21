from unittest import TestCase

from pyramid import testing
from repoze.folder.events import ObjectAddedEvent
from zope.component.event import objectEventNotify

from voteit.core.security import ROLE_MODERATOR
from voteit.core.security import ROLE_VOTER


class MeetingSubscriberTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _make_obj(self):
        from voteit.core.models.meeting import Meeting
        return Meeting

    def test_generate_email_hash(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        self.config.scan('voteit.core.subscribers.meeting')
        self.config.testing_securitypolicy(userid='some_user',
                                           permissive=True)

        obj = self._make_obj()
        objectEventNotify(ObjectAddedEvent(obj, None, 'dummy'))
        
        self.assertTrue(ROLE_MODERATOR in obj.get_groups('some_user'))
        self.assertTrue(ROLE_VOTER in obj.get_groups('some_user'))

