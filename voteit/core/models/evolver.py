from arche.models.evolver import BaseEvolver

from voteit.core.evolve import VERSION


class VoteITCoreEvolver(BaseEvolver):
    name = 'voteit.core'
    sw_version = VERSION
    initial_db_version = 8


def includeme(config):
    config.add_evolver(VoteITCoreEvolver)
