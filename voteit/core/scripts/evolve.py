import sys

from repoze.evolution import ZODBEvolutionManager
from repoze.evolution import evolve_to_latest

from voteit.core.scripts.worker import ScriptWorker
from voteit.core.evolve import VERSION

def main(argv=sys.argv):
    worker = ScriptWorker('evolve')
    root = worker.root
    
    print 'Evolve site'
    manager = ZODBEvolutionManager(root, evolve_packagename='voteit.core.evolve', sw_version=VERSION, initial_db_version=0)
    ver = manager.get_db_version()
    if ver < VERSION:
        evolve_to_latest(manager)
        print 'Evolved from %s to %s' % (ver, manager.get_db_version())
    else:
        print 'Already evolved to latest version'
    
    worker.shutdown()