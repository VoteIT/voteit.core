import transaction
import sys

from voteit.core.scripts.worker import ScriptWorker


def debug_instance(*args):
    worker = ScriptWorker('debug')
    root = worker.root
    print "worker contains script stuff. root is root"
    import pdb;pdb.set_trace()
    worker.shutdown()
