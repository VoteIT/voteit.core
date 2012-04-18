import unittest
from datetime import datetime

import colander
from pyramid import testing

from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.testing_helpers import bootstrap_and_fixture


class CommonSchemaTests(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request = self.request)

    def tearDown(self):
        testing.tearDown()

    def test_deferred_default_start_time(self):
        from voteit.core.schemas.common import deferred_default_start_time as fut
        settings = self.config.registry.settings
        settings['default_locale_name'] = 'sv'
        settings['default_timezone_name'] = 'Europe/Stockholm'
        self.config.include('voteit.core.models.date_time_util')
        res = fut(None, {'request': self.request})
        self.assertIsInstance(res, datetime)
        self.assertTrue(hasattr(res, 'tzinfo'))

    def test_deferred_default_end_time(self):
        from voteit.core.schemas.common import deferred_default_end_time as fut
        settings = self.config.registry.settings
        settings['default_locale_name'] = 'sv'
        settings['default_timezone_name'] = 'Europe/Stockholm'
        self.config.include('voteit.core.models.date_time_util')
        res = fut(None, {'request': self.request})
        self.assertIsInstance(res, datetime)
        self.assertTrue(hasattr(res, 'tzinfo'))

    def test_deferred_default_user_fullname(self):
        from voteit.core.schemas.common import deferred_default_user_fullname as fut
        from voteit.core.views.api import APIView
        root = bootstrap_and_fixture(self.config)
        admin = root.users['admin']
        admin.set_field_value('first_name', 'Jane')
        admin.set_field_value('last_name', 'Doe')
        self.config.testing_securitypolicy(userid='admin')
        kw = {'api': APIView(root, self.request)}
        self.assertEqual(fut(None, kw), 'Jane Doe')
        self.config.testing_securitypolicy(userid='404')
        kw = {'api': APIView(root, self.request)}
        self.assertEqual(fut(None, kw), '')

    def test_deferred_default_user_email(self):
        from voteit.core.schemas.common import deferred_default_user_email as fut
        from voteit.core.views.api import APIView
        root = bootstrap_and_fixture(self.config)
        admin = root.users['admin']
        admin.set_field_value('email', 'hello_world@betahaus.net')
        self.config.testing_securitypolicy(userid='admin')
        kw = {'api': APIView(root, self.request)}
        self.assertEqual(fut(None, kw), 'hello_world@betahaus.net')
        self.config.testing_securitypolicy(userid='404')
        kw = {'api': APIView(root, self.request)}
        self.assertEqual(fut(None, kw), '')
