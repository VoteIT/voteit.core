from arche.models.evolver import BaseEvolver

from voteit.core.evolve import VERSION


class VoteITCoreEvolver(BaseEvolver):
    name = 'voteit.core'
    sw_version = VERSION


def includeme(config):
    config.add_evolver(VoteITCoreEvolver)
