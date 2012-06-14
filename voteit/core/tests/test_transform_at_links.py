from unittest import TestCase

from repoze.folder.events import ObjectAddedEvent
from pyramid import testing
from zope.component.event import objectEventNotify

from voteit.core.testing_helpers import bootstrap_and_fixture


class TransformAtLinksTests(TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.helpers import at_userid_link
        return at_userid_link

    def _fixture(self):
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.user import User
        root = bootstrap_and_fixture(self.config)
        root['m'] = Meeting()
        root['users']['dummy'] = User(first_name = 'John', last_name = 'Doe')
        return root

    def test_transform_mention(self):
        root = self._fixture()
        root['m']['c'] = context = testing.DummyModel()
        expected = '<a class="inlineinfo" href="/m/_userinfo?userid=dummy" title="John Doe">@dummy</a>'
        self.assertEqual(self._fut('@dummy', context), expected)

    def test_several_results(self):
        root = self._fixture()
        root['m']['c'] = context = testing.DummyModel()
        result = self._fut('@dummy @admin', context)
        self.failUnless('John Doe' in result)
        self.failUnless('Administrator' in result)
        
    def test_transform_mention_uppercase(self):
        root = self._fixture()
        root['m']['c'] = context = testing.DummyModel()
        expected = '<a class="inlineinfo" href="/m/_userinfo?userid=dummy" title="John Doe">@dummy</a>'
        self.assertEqual(self._fut('@Dummy', context), expected)

    #FIXME: We need more tests
