
from arche.interfaces import IObjectUpdatedEvent
from arche.interfaces import IWillLoginEvent
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


def use_provider_image_if_none_present(event):
    provider_name = getattr(event, 'provider', None)
    if not provider_name:
        return
    if event.user.profile_image_plugin:
        return
    request = getattr(event, 'request', get_current_request())
    provider = request.registry.queryAdapter(request, IPASProvider, name=provider_name)
    data = IProviderData(event.user, {})
    img_url = provider.get_profile_image(data.get(provider_name, {}))
    if img_url:
        event.user.profile_image_plugin = "pas_image_%s" % provider_name


def remove_image_if_pas_removed(user, event):
    if 'pas_ident' not in getattr(event, 'changed', ()):
        return
    data = IProviderData(user, {})
    if user.profile_image_plugin and user.profile_image_plugin not in data:
        user.profile_image_plugin = ""


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
                config.registry.registerAdapter(_Adapter, name = _Adapter.name)
    else:
        raise ImportError("arche_pas not included")
    config.add_subscriber(use_provider_image_if_none_present, IWillLoginEvent)
    config.add_subscriber(remove_image_if_pas_removed, [IUser, IObjectUpdatedEvent])
