#from babel.core import Locale
from pyramid.i18n import get_locale_name
from pyramid.threadlocal import get_current_request
from babel.dates import format_date
from babel.dates import format_datetime
#from babel.dates import format_time

from zope.interface import implements

from voteit.core.models.interfaces import IDateTimeUtil


class DateTimeUtil(object):
    """ Handle conversion and printing of date and time.
        See IDateTimeUtil
    """
    implements(IDateTimeUtil)
    locale = None
    
    def __init__(self, locale='en'):
        self.set_locale(locale)
    
    def set_locale(self, value):
        self.locale = value
    
    def date(self, value, format='short'):
        return format_date(value, format=format, locale=self.locale)

    def datetime(self, value, format='short'):
        return format_datetime(value, format=format, locale=self.locale)
