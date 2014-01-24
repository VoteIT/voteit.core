
def includeme(config):
    """ Include this to activate password login. """
    from .models import PasswordAuth
    from .models import PasswordHandler
    config.registry.registerAdapter(PasswordAuth, name = PasswordAuth.name)
    config.registry.registerAdapter(PasswordHandler)
    config.scan(__name__)
