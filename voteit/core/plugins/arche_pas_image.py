try:
    from arche_pas.interfaces import IProviderData
    from arche_pas.interfaces import IPASProvider
    _enabled = True
except ImportError:
    _enabled = False
from pyramid.threadlocal import get_current_request
from zope.interface import implementer
from zope.component import adapter

from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IProfileImage


@implementer(IProfileImage)
@adapter(IUser)
class PASImagePlugin(object):
    name = ''
    pas_name = ''
    title = ''
    description = ''

    def __init__(self, context):
        self.context = context
        self.provider_data = IProviderData(self.context)

    def url(self, size, request):
        provider = request.registry.getAdapter(request, IPASProvider, name=self.pas_name)
        return provider.get_profile_image(self.provider_data.get(self.pas_name, {}))

    def is_valid_for_user(self):
        request = get_current_request()
        provider = request.registry.getAdapter(request, IPASProvider, name=self.pas_name)
        return bool(provider.get_profile_image(self.provider_data.get(self.pas_name, {})))


def includeme(config):
    """ Include plugins matching IPASProvider adapters
    """
    if _enabled:
        for ar in config.registry.registeredAdapters():
            if ar.provided == IPASProvider:
                #Register new adapter
                class _Adapter(PASImagePlugin):
                    name = "pas_image_%s" % ar.name
                    pas_name = ar.name
                    title = ar.factory.title
                #IPASProvider
                config.registry.registerAdapter(_Adapter, name = _Adapter.name)
    else:
        raise ImportError("arche_pas not included")
