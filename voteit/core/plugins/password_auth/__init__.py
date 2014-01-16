
def includeme(config):
    """ Include this to activate password login. """
    from .models import PasswordAuth
    config.registry.registerAdapter(PasswordAuth, name = PasswordAuth.name)
    config.scan()
