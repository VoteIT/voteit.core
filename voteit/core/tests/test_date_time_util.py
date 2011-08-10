import unittest
from datetime import datetime

import pytz

from pyramid import testing
from zope.interface.verify import verifyObject
from voteit.core.models.interfaces import IDateTimeUtil


class DateTimeUtilityTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _make_obj(self):
        from voteit.core.models.date_time_util import DateTimeUtil
        return DateTimeUtil()

    def test_verify_obj(self):
        obj = self._make_obj()
        self.assertTrue(verifyObject(IDateTimeUtil, obj))

    def test_add_method(self):
        from voteit.core.app import add_date_time_util
        
        add_date_time_util(self.config, locale='sv', timezone_name='Europe/Stockholm')
        util = self.config.registry.queryUtility(IDateTimeUtil)
        
        self.failUnless(util)
    
    def test_d_format(self):
        obj = self._make_obj()
        date = obj.localize(datetime.strptime('1999-12-13', "%Y-%m-%d"))
        self.assertEqual(obj.d_format(date), u'12/13/99')
    
    def test_dt_format(self):
        obj = self._make_obj()
        date_and_time = obj.localize(datetime.strptime('1999-12-14 19:12', "%Y-%m-%d %H:%M"))
        self.assertEqual(obj.dt_format(date_and_time), '12/14/99 7:12 PM')
    
    def test_datetime_sv_locale(self):
        obj = self._make_obj()
        obj.set_locale('sv')
        date_and_time = obj.localize(datetime.strptime('1999-12-14 19:12', "%Y-%m-%d %H:%M"))
        self.assertEqual(obj.dt_format(date_and_time), '1999-12-14 19.12')

    def test_datetime_full_sv(self):
        obj = self._make_obj()
        obj.set_locale('sv')
        date_and_time = obj.localize(datetime.strptime('1999-12-14 19:12', "%Y-%m-%d %H:%M"))
        self.assertEqual(obj.dt_format(date_and_time, format='full'), u'tisdag den 14 december 1999 kl. 19.12.00 Sverige')

    def test_datetime_localize(self):
        obj = self._make_obj()
        fmt = '%Y-%m-%d %H:%M %Z%z'
        date_time = datetime.strptime('1999-12-14 19:12', "%Y-%m-%d %H:%M")
        localized_dt = obj.localize(date_time)
        result = localized_dt.strftime(fmt)
        self.assertEquals(result, '1999-12-14 19:12 CET+0100')

    def test_tz_to_utc(self):
        obj = self._make_obj()
        fmt = '%Y-%m-%d %H:%M %Z%z'
        date_time = datetime.strptime('1999-12-14 19:12', "%Y-%m-%d %H:%M")
        localized_dt = obj.localize(date_time)
        utc_dt = obj.tz_to_utc(localized_dt)
        result = utc_dt.strftime(fmt)
        self.assertEquals(result, '1999-12-14 18:12 UTC+0000')

    def test_utc_to_tz(self):
        obj = self._make_obj()
        fmt = '%Y-%m-%d %H:%M %Z%z'
        date_time = datetime.strptime('1999-12-14 18:12', "%Y-%m-%d %H:%M")
        utc_dt = obj.localize(date_time, pytz.utc)
        local_dt = obj.utc_to_tz(utc_dt)
        result = local_dt.strftime(fmt)
        self.assertEquals(result, '1999-12-14 19:12 CET+0100')

    def test_utcnow(self):
        from voteit.core.models.date_time_util import utcnow
        obj = self._make_obj()
        now = utcnow()
        self.assertEquals(now.tzinfo, pytz.utc)
        now = obj.utcnow()
        self.assertEquals(now.tzinfo, pytz.utc)

    def test_localnow(self):
        obj = self._make_obj()
        now = obj.localnow()
        # we don't check for exactly equal timezones due to DST changes
        self.assertEquals(str(now.tzinfo), str(obj.timezone))
