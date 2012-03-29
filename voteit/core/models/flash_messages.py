from pyramid.interfaces import IRequest
from zope.interface import implements

from voteit.core.models.interfaces import IFlashMessages


class FlashMessages(object):
    """ See :mod:`voteit.core.models.interfaces.IFlashMessages`
    """
    implements(IFlashMessages)
    
    def __init__(self, request):
        self.request = request

    def add(self, msg, type='info', close_button=True):
        flash = {'msg':msg, 'type':type, 'close_button':close_button}
        self.request.session.flash(flash)

    def get_messages(self):
        for message in self.request.session.pop_flash():
            yield message


def includeme(config):
    """ Include FlashMessages adapter in registry.
        Call this by running config.include('voteit.core.models.flash_messages')
    """
    config.registry.registerAdapter(FlashMessages, (IRequest,), IFlashMessages)
