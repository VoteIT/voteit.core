from zope.interface import implements
from fanstatic import Group
from fanstatic import Resource

from voteit.core.models.interfaces import IFanstaticResources


class FanstaticResources(object):
    """ See :mod:`voteit.core.models.interfaces.IFanstaticResources`.
    """
    implements(IFanstaticResources)

    def __init__(self):
        self.order = []
        self.resources = {}
        self.discriminators = {}

    def add(self, key, resource, discriminator = None):
        if not isinstance(resource, Group) and not isinstance(resource, Resource):
            raise TypeError("'resource' must be a Fanstatic Group or a Resource class. Got: %s" % resource)
        self.order.append(key)
        self.resources[key] = resource
        if discriminator is not None:
            if not callable(discriminator):
                raise TypeError("'discriminator' must be a callable that accepts a context and a request as argument.")
            self.discriminators[key] = discriminator

    def include_needed(self, context, request, view):
        needed = []
        for key in self.order:
            if key in self.discriminators:
                if not self.discriminators[key](context, request, view):
                    continue
            self.resources[key].need()
            needed.append(key)
        return needed


def includeme(config):
    """ Register utility. This method is used when you include this
        module with a Pyramid configurator. This specific module
        will be included as default by VoteIT.
    """
    config.registry.registerUtility(FanstaticResources(), IFanstaticResources)
