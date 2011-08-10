#from babel.core import Locale
from pyramid.i18n import get_locale_name
from pyramid.threadlocal import get_current_request
from babel.dates import format_date
from babel.dates import format_datetime
#from babel.dates import format_time

import pytz
from pytz import timezone
from datetime import datetime

from zope.interface import implements

from voteit.core.models.interfaces import IDateTimeUtil


class DateTimeUtil(object):
    """ Handle conversion and printing of date and time.
        See IDateTimeUtil
    """
    implements(IDateTimeUtil)
    locale = None
    timezone_name = None

    def __init__(self, locale='en', timezone_name='Europe/Stockholm'):
        self.set_locale(locale)
        self.timezone = timezone(timezone_name)

    def set_locale(self, value):
        self.locale = value

    def d_format(self, value, format='short'):
        """ Format the given date in the given format.
            Will also convert to current timezone from utc.
        """
        localtime = self.utc_to_tz(value)
        return format_date(localtime, format=format, locale=self.locale)

    def dt_format(self, value, format='short'):
        """ Format the given datetime in the given format.
            Will also convert to current timezone from utc.
        """
        localtime = self.utc_to_tz(value)
        return format_datetime(localtime, format=format, locale=self.locale)

    def tz_to_utc(self, datetime):
        """Convert the provided datetime object from local to UTC.

        The datetime object is expected to have the timezone specified in
        the timezone attribute.
        """
        utc = pytz.utc
        return datetime.astimezone(utc)

    def utc_to_tz(self, datetime):
        """Convert the provided datetime object from UTC to local.

        The resulting localized datetime object will have the timezone
        specified in the timezone attribute.
        """

        return self.timezone.normalize(datetime.astimezone(self.timezone))

    def localize(self, datetime, tz=None):
        """Localize a naive datetime to the provided timezone.

        If no timezone is provided, the current selected one is used.
        
        Example usage:
        from datetime.datetime import now
        #Regular python datetime:
        now_dt = now()
        #Converted to datetime that cares about a specific locale:
        self.localize(now_dt)
        """

        if tz is None:
            tz = self.timezone

        return tz.localize(datetime)

    def utcnow(self):
        """Get the current datetime localized to UTC.

        The difference between this method and datetime.utcnow() is
        that datetime.utcnow() returns the current UTC time but as a naive
        datetime object, whereas this one includes the UTC tz info.
        """
        naive_utcnow = datetime.utcnow()
        return self.localize(naive_utcnow, pytz.utc)
