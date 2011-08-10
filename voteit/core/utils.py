from pyramid.threadlocal import get_current_registry
from voteit.core.models.interfaces import IDateTimeUtil


def getDateTimeUtil():
    """Get the date time util to localize times and convert between timezones
    from the current registry.
    """

    registry = get_current_registry()
    return registry.getUtility(IDateTimeUtil)
