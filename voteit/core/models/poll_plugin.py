from zope.interface import implements
from zope.component import adapts

from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin


class PollPlugin(object):
    """ Base class for poll plugins. Subclass this to make your own.
        It's not usable by itself, since it doesn't implement the required interfaces.
        See IPollPlugin for documentation.
    """
    implements(IPollPlugin)
    adapts(IPoll)
    
    def __init__(self, context):
        self.context = context