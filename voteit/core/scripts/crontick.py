from calendar import timegm

import transaction
from pyramid.util import DottedNameResolver

from voteit.core.scripts.worker import ScriptWorker
from voteit.core.models.date_time_util import utcnow


def _find_methods(worker):
    cronjobsentry = worker.app.registry.settings.get('cronjobs')
    if cronjobsentry is None:
        raise ValueError("cronjobs must exist in application configuration if you want to run this. "
                         "It should point to methods that can be run by the crontick worker. "
                         "See voteit.core.scripts.crontick")

    resolver = DottedNameResolver(None)

    dotteds = [x.strip() for x in cronjobsentry.strip().splitlines()]
    methods = []
    for dotted in dotteds:
        try:
            methods.append(resolver.resolve(dotted))
        except ImportError, e:
            worker.logger.exception(e)
    return methods

def crontick():
    
    worker = ScriptWorker('crontick')
    
    unixnow = timegm(utcnow().timetuple())

    #Find methods to execute and run them
    methods = _find_methods(worker)
    
    for method in methods:
        try:
            method(worker, unixnow)
            transaction.commit()
            print "=== Transaction for %s committed" % method
        except Exception, e:
            worker.logger.exception(e)
            transaction.abort()
            print "=== Transaction for %s aborted" % method
    
    worker.shutdown()
    