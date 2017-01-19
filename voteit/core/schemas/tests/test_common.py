# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import unittest
from datetime import datetime

from pyramid import testing
from pyramid.request import Request
from arche.models.datetime_handler import DateTimeHandler

from voteit.core.testing_helpers import bootstrap_and_fixture


class CommonSchemaTests(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.request.dt_handler = DateTimeHandler(self.request, tz_name = 'Europe/Stockholm')
        self.config = testing.setUp(request = self.request)

    def tearDown(self):
        testing.tearDown()

    def test_deferred_default_start_time(self):
        from voteit.core.schemas.common import deferred_default_start_time as fut
        res = fut(None, {'request': self.request})
        self.assertIsInstance(res, datetime)
        self.assertTrue(hasattr(res, 'tzinfo'))

    def test_deferred_default_end_time(self):
        from voteit.core.schemas.common import deferred_default_end_time as fut
        res = fut(None, {'request': self.request})
        self.assertIsInstance(res, datetime)
        self.assertTrue(hasattr(res, 'tzinfo'))

    def test_deferred_default_user_fullname(self):
        from voteit.core.schemas.common import deferred_default_user_fullname as fut
        root = bootstrap_and_fixture(self.config)
        admin = root.users['admin']
        admin.first_name = 'Jane'
        admin.last_name = 'Doe'
        self.request.profile = admin
        kw = {'request': self.request}
        self.assertEqual(fut(None, kw), 'Jane Doe')
        self.request.profile = None
        self.assertEqual(fut(None, kw), '')

    def test_deferred_default_user_email(self):
        from voteit.core.schemas.common import deferred_default_user_email as fut
        root = bootstrap_and_fixture(self.config)
        admin = root.users['admin']
        admin.email = 'hello_world@betahaus.net'
        self.request.profile = admin
        kw = {'request': self.request}
        self.assertEqual(fut(None, kw), 'hello_world@betahaus.net')
        self.request.profile = None
        kw = {'request': self.request}
        self.assertEqual(fut(None, kw), '')


class DeferredDefaultHashtagTextTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('voteit.core.models.proposal_ids')

    def tearDown(self):
        testing.tearDown()

    @property
    def _fut(self):
        from voteit.core.schemas.common import deferred_default_hashtag_text
        return deferred_default_hashtag_text

    def _fixture(self):
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.discussion_post import DiscussionPost
        from voteit.core.models.proposal import Proposal
        from voteit.core.models.meeting import Meeting
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        ai['p1'] = Proposal(text = "I dream of a #free world", creator = ['admin'])
        ai['p2'] = Proposal(text = "#free as in #freedom, not #free #beer", creator = ['admin'])
        ai['d1'] = DiscussionPost(text = "I agree with #admin-2", creator = ['admin'])
        return root

    def test_new_blank(self):
        root = self._fixture()
        request = Request.blank('/')
        request.root = root
        self.assertEqual(self._fut(None, {'request': request}), "")

    def test_tags_in_request(self):
        root = self._fixture()
        request = Request.blank('/', )
        request.GET.add('tag', 'one')
        request.GET.add('tag', 'two')
        request.root = root
        self.assertEqual(self._fut(None, {'request': request}), "#one #two")

    def test_tags_from_reply(self):
        self.config.include('arche.testing')
        self.config.include('arche.models.catalog')
        root = self._fixture()
        request = Request.blank('/')
        uid = root['m']['ai']['p2'].uid
        request.GET.add('reply-to', uid)
        request.root = root
        self.assertEqual(self._fut(None, {'request': request}), "#free #freedom #beer #admin-2")

    def test_reply_to_discussion_includes_creator(self):
        self.config.include('arche.testing')
        self.config.include('arche.models.catalog')
        root = self._fixture()
        request = Request.blank('/')
        uid = root['m']['ai']['d1'].uid
        request.GET.add('reply-to', uid)
        request.root = root
        self.assertEqual(self._fut(None, {'request': request}), "@admin: #admin-2")

    def test_all_together(self):
        self.config.include('arche.testing')
        self.config.include('arche.models.catalog')
        root = self._fixture()
        request = Request.blank('/')
        uid = root['m']['ai']['d1'].uid
        request.GET.add('reply-to', uid)
        request.GET.add('tag', 'rainbows')
        request.GET.add('tag', 'unicorns')
        request.root = root
        self.assertEqual(self._fut(None, {'request': request}), "@admin: #rainbows #unicorns #admin-2")
