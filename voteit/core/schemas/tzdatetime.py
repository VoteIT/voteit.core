import datetime
import iso8601

from zope.component import getUtility
from colander import SchemaType
from colander import Invalid
from colander import null

from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core import VoteITMF as _


class TZDateTime(SchemaType):
    """ A type representing a timezone-aware datetime object.

    It respects the timezone specified on creation. The datetime coming from
    the form is expected to be specified according to the local time zone, and
    is converted to UTC during deserialization. Serialization converts it back
    to the local timezone, so the conversion process is transparent to the user.
    """
    def serialize(self, node, appstruct):
        dt_util = getUtility(IDateTimeUtil)
        if appstruct is null:
            return null

        if type(appstruct) is datetime.date: # cant use isinstance; dt subs date
            appstruct = datetime.datetime.combine(appstruct, datetime.time())

        if not isinstance(appstruct, datetime.datetime):
            raise Invalid(node,
                          _("'${val}' is not valid as date and time",
                            mapping={'val':appstruct})
                          )
        #FIXME: Don't use strftime, util already has a method for that
        #FIXME: Output format must be taken from the current locale
        return dt_util.utc_to_tz(appstruct).strftime('%Y-%m-%d %H:%M')

    def deserialize(self, node, cstruct):
        dt_util = getUtility(IDateTimeUtil)
        if not cstruct:
            return null

        try:
            #FIXME: Imput format must be from the current locale
            result = datetime.datetime.strptime(cstruct, "%Y-%m-%dT%H:%M")

            # python's datetime doesn't deal correctly with DST, so we have
            # to use the pytz localize function instead
            result = result.replace(tzinfo=None)
            result = dt_util.localize(result)

        except (iso8601.ParseError, TypeError), e:
            try:
                year, month, day = map(int, cstruct.split('-', 2))
                result = datetime.datetime(year, month, day,
                                           tzinfo=self.default_tzinfo)
            except Exception, e:
                raise Invalid(node, _(self.err_template,
                                      mapping={'val':cstruct, 'err':e}))

        return dt_util.tz_to_utc(result)
