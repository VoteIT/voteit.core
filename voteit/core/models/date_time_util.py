from datetime import datetime

import pytz
from babel.dates import format_date
from babel.dates import format_time
from babel.dates import format_datetime
from zope.interface import implements
from arche.utils import utcnow

from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core import VoteITMF as _



# class DateTimeUtil(object):
#     """ Handle conversion and printing of date and time.
#         See :mod:`voteit.core.models.interfaces.IDateTimeUtil`.
#     """
#     implements(IDateTimeUtil)
#     locale = None
#     timezone_name = None
# 
#     def __init__(self, locale='en', timezone_name='Europe/Stockholm'):
#         """ Initialize util. """
#         #FIXME: get default timezone instead of Europe/Stockholm
#         self.set_locale(locale)
#         self.timezone = pytz.timezone(timezone_name)
# 
#     def set_locale(self, value):
#         """ Set the locale. """
#         self.locale = value
# 
#     def d_format(self, value, format='short'):
#         """ Format the given date in the given format.
#             Will also convert to current timezone from utc.
#         """
#         localtime = self.utc_to_tz(value)
#         return format_date(localtime, format=format, locale=self.locale)
# 
#     def t_format(self, value, format='short'):
#         """ Format time in the givet format.
#             Will also convert to current timezone from utc.
#         """
#         localtime = self.utc_to_tz(value)
#         return format_time(localtime, format=format, locale=self.locale)
#     
#     def dt_format(self, value, format='short'):
#         """ Format the given datetime in the given format.
#             Will also convert to current timezone from utc.
#         """
#         localtime = self.utc_to_tz(value)
#         return format_datetime(localtime, format=format, locale=self.locale)
# 
#     def tz_to_utc(self, datetime):
#         """Convert the provided datetime object from local to UTC.
# 
#         The datetime object is expected to have the timezone specified in
#         the timezone attribute.
#         """
#         utc = pytz.utc
#         return datetime.astimezone(utc)
# 
#     def utc_to_tz(self, datetime):
#         """Convert the provided datetime object from UTC to local.
# 
#         The resulting localized datetime object will have the timezone
#         specified in the timezone attribute.
#         """
# 
#         return self.timezone.normalize(datetime.astimezone(self.timezone))
# 
#     def localize(self, datetime, tz=None):
#         """Localize a naive datetime to the provided timezone.
# 
#         If no timezone is provided, the current selected one is used.
#         
#         Example usage:
#         from datetime.datetime import now
#         #Regular python datetime:
#         now_dt = now()
#         #Converted to datetime that cares about a specific locale:
#         self.localize(now_dt)
#         """
# 
#         if tz is None:
#             tz = self.timezone
# 
#         return tz.localize(datetime)
# 
#     def localnow(self, tz=None):
#         """Get the current datetime localized to the specified timezone.
#         If no timezone is specified, the current selected one is used.
#         """
#         naive_now = datetime.now()
# 
#         if tz is None:
#             tz = self.timezone
# 
#         return self.localize(naive_now, tz)
# 
#     def utcnow(self):
#         """ Same as :func:`utcnow` """
#         return utcnow()
# 
#     def relative_time_format(self, time):
#         """ Get a datetime object or a int() Epoch timestamp and return a
#             pretty string like 'an hour ago', 'Yesterday', '3 months ago',
#             'just now', etc
#         """
#         if isinstance(time, int):
#             time = datetime.fromtimestamp(time, pytz.utc)
#         #Check if timezone is naive, convert
#         if time.tzinfo is None:
#             raise ValueError("Not possible to use relative_time_format with timezone naive datetimes.")
#         elif time.tzinfo is not pytz.utc:
#             time = self.tz_to_utc(time)
# 
#         now = self.utcnow()
#         diff = now - time
#         second_diff = diff.seconds
#         day_diff = diff.days
# 
#         if day_diff < 0:
#             #FIXME: Shouldn't future be handled as well? :)
#             return self.dt_format(time)
# 
#         if day_diff == 0:
#             if second_diff < 10:
#                 return _("Just now")
#             if second_diff < 60:
#                 return _("${diff} seconds ago", mapping={'diff': str(second_diff)})
#             if second_diff < 120:
#                 return  _("1 minute ago")
#             if second_diff < 3600:
#                 return _("${diff} minutes ago", mapping={'diff': str(second_diff / 60)})
#             if second_diff < 7200:
#                 return _("1 hour ago")
#             if second_diff < 86400:
#                 return _("${diff} hours ago", mapping={'diff': str(second_diff / 3600)})
# 
#         #If it's longer than 7 days, just run the regular localization
#         return self.dt_format(time)


def includeme(config):
    """ Register utility. This method is used when you include this
        module with a Pyramid configurator. This specific module
        will be included as default by VoteIT.
    """
    pass
    #locale = config.registry.settings['default_locale_name']
    #timezone_name = config.registry.settings['default_timezone_name']
    #util = DateTimeUtil(locale, timezone_name)
    #config.registry.registerUtility(util, IDateTimeUtil)
