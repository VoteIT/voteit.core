import datetime
import iso8601

from pyramid.threadlocal import get_current_registry
from colander import DateTime, Invalid, null, _
from voteit.core.models.interfaces import IDateTimeUtil


class TZDateTime(DateTime):
    """ A type representing a timezone-aware datetime object.

    It respects the timezone specified on creation.
    """

    def serialize(self, node, appstruct):
        if appstruct is null:
            return null

        if type(appstruct) is datetime.date: # cant use isinstance; dt subs date
            appstruct = datetime.datetime.combine(appstruct, datetime.time())

        if not isinstance(appstruct, datetime.datetime):
            raise Invalid(node,
                          _('"${val}" is not a datetime object',
                            mapping={'val':appstruct})
                          )

        registry = get_current_registry()
        dt_util = registry.getUtility(IDateTimeUtil)
        return dt_util.utc_to_tz(appstruct).isoformat()

        # if appstruct.tzinfo is None:
        #     appstruct = appstruct.replace(tzinfo=self.default_tzinfo)
        # return appstruct.isoformat()


    def deserialize(self, node, cstruct):
        registry = get_current_registry()
        dt_util = registry.getUtility(IDateTimeUtil)

        if not cstruct:
            return null
        
        try:
            result = iso8601.parse_date(cstruct, self.default_tzinfo)
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

        result = dt_util.tz_to_utc(result)

        return result
