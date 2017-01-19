from arche.interfaces import IFlashMessages as AIFM
from pyramid.interfaces import IRequest
from zope.interface import implementer

from voteit.core.models.interfaces import IFlashMessages


@implementer(IFlashMessages)
class FlashMessages(object):
    """ See :mod:`voteit.core.models.interfaces.IFlashMessages`
    """
    
    def __init__(self, request):
        self.request = request

    def add(self, msg, type='info', close_button=True):
        """ Delegate to arches flash messages."""
        fm = self.request.registry.queryAdapter(self.request, AIFM)
        if not fm:
            from arche.models.flash_messages import FlashMessages
            fm = FlashMessages(self.request)
        fm.add(msg, type = type)
        #flash = {'msg':msg, 'type':type, 'close_button':close_button}
        #self.request.session.flash(flash)

    def get_messages(self):
        for message in self.request.session.pop_flash():
            yield message


def includeme(config):
    """ Include FlashMessages adapter in registry.
        Call this by running config.include('voteit.core.models.flash_messages')
    """
    config.registry.registerAdapter(FlashMessages, (IRequest,), IFlashMessages)
