import unittest
from datetime import datetime

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
        
        add_date_time_util(self.config, locale='sv')
        util = self.config.registry.queryUtility(IDateTimeUtil)
        
        self.failUnless(util)
    
    def test_date(self):
        obj = self._make_obj()
        date = datetime.strptime('1999-12-13', "%Y-%m-%d")
        self.assertEqual(obj.date(date), u'12/13/99')
    
    def test_datetime(self):
        obj = self._make_obj()
        date_and_time = datetime.strptime('1999-12-14 19:12', "%Y-%m-%d %H:%M")
        self.assertEqual(obj.datetime(date_and_time), '12/14/99 7:12 PM')
    
    def test_datetime_sv_locale(self):
        obj = self._make_obj()
        obj.set_locale('sv')
        date_and_time = datetime.strptime('1999-12-14 19:12', "%Y-%m-%d %H:%M")
        self.assertEqual(obj.datetime(date_and_time), '1999-12-14 19.12')

    def test_datetime_full_sv(self):
        obj = self._make_obj()
        obj.set_locale('sv')
        date_and_time = datetime.strptime('1999-12-14 19:12', "%Y-%m-%d %H:%M")
        self.assertEqual(obj.datetime(date_and_time, format='full'), u'tisdag den 14 december 1999 kl. 19.12.00 v\xe4rlden (GMT)')
        