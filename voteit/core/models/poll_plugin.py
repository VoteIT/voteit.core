from zope.interface import implements
from voteit.core.models.interfaces import IPollPlugin


class PollPlugin(object):
    """ Base class for poll plugins. Subclass this to make your own.
        It's not usable by itself, since it doesn't implement the required interfaces.
        See IPollPlugin for documentation.
    """
    implements(IPollPlugin)
    