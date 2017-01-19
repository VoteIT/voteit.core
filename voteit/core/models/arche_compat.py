from BTrees.OOBTree import OOBTree

from arche.utils import get_content_factories


def createContent(type_name, *args, **kw):
    """ Replaces the betahaus.pyracont createContent method with a wrapper for Arches
        factory implementation.
    """
    factories = get_content_factories()
    return factories[type_name](*args, **kw)
