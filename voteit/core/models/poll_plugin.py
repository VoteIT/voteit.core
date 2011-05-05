#from zope.component import adapts
from zope.interface import implements

from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin


class PollPlugin(object):
    implements(IPollPlugin)
#    adapts(IPoll)
    
    name = u'base_plugin_type'
    title = u'Base Plugin'
    
    