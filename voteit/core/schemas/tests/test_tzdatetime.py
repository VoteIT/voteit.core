import unittest
from datetime import date
from datetime import datetime

import colander
from pyramid import testing

from voteit.core.models.interfaces import IDateTimeUtil


class TZDateTimeTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.registry.settings['default_locale_name'] = 'en'
        self.config.registry.settings['default_timezone_name'] = "Europe/Stockholm"
        self.config.include('voteit.core.models.date_time_util')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.core.schemas.tzdatetime import TZDateTime
        return TZDateTime

    def test_serialize_datetime(self):
        obj = self._cut()
        dt_util = self.config.registry.getUtility(IDateTimeUtil)
        dt = dt_util.localize(datetime.strptime('2005-03-05 23:00', "%Y-%m-%d %H:%M"))
        self.assertEqual(obj.serialize(None, dt), '2005-03-05 23:00')

    def test_serialize_date(self):
        obj = self._cut()
        self.assertEqual(obj.serialize(None, date(2005, 03, 05)), '2005-03-05 00:00')

    def test_serialize_bad_datetime(self):
        obj = self._cut()
        now = datetime.now()
        self.assertRaises(ValueError, obj.serialize, None, now)        

    def test_serialize_null(self):
        obj = self._cut()
        self.assertEqual(obj.serialize(None, colander.null), colander.null)

    def test_serialize_bad_data(self):
        obj = self._cut()
        self.assertRaises(colander.Invalid, obj.serialize, None, 'Hello!')

    def test_deserialize_null(self):
        obj = self._cut()
        self.assertEqual(obj.deserialize(None, colander.null), colander.null)

    def test_deserialize(self):
        import pytz
        obj = self._cut()
        dt = "2005-03-05T23:00"
        res = obj.deserialize(None, dt)
        self.assertEqual(res.tzinfo, pytz.utc)

    def test_deserialize_bad_input(self):
        obj = self._cut()
        self.assertRaises(colander.Invalid, obj.deserialize, None, 'Hello!')
