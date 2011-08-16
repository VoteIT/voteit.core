""" This contains methods that should be executed by the crontick script.
    (Found at scripts/crontick.py)
    The argument passed to them will be a script worker - it contains
    configuration and the app root.
    Since these are cron jobs, unixnow is passed as well, which is a unix time
    representation of "utc now".
    See scripts/worker.py for more info.
    
    Any exceptions will be handled by the worker rather than in this script.
"""
from pyramid.traversal import find_resource

from voteit.core.security import unrestricted_wf_transition_to


def open_polls(worker, unixnow):
    """ Start polls that are inactive and have passed their start time. """
    print "=== Open running"
    cat = worker.root.catalog
    res_addr = cat.document_map.address_for_docid
    
    q_str = "start_time <= %s and workflow_state == 'planned' and content_type == 'Poll'" % unixnow
    for id in cat.query(q_str)[1]:
        path = res_addr(id)
        obj = find_resource(worker.root, path)
        unrestricted_wf_transition_to(obj, 'ongoing')
        worker.logger.info("Setting 'ongoing' state for poll at: %s" % path)

def close_polls(worker, unixnow):
    """ Close open polls that have passed their end time. """
    print "=== Close running"
    cat = worker.root.catalog
    res_addr = cat.document_map.address_for_docid
    
    q_str = "end_time <= %s and workflow_state == 'ongoing' and content_type == 'Poll'" % unixnow
    for id in cat.query(q_str)[1]:
        path = res_addr(id)
        obj = find_resource(worker.root, path)
        unrestricted_wf_transition_to(obj, 'closed')
        worker.logger.info("Setting 'closed' state for poll at: %s" % path)
