from calendar import timegm

import transaction
from pyramid.traversal import find_resource

from voteit.core.scripts.worker import ScriptWorker
from voteit.core.models.date_time_util import utcnow
from voteit.core.security import unrestricted_wf_transition_to


def crontick():
    #FIXME: Needs to be very defensive and handle exceptions    
    
    worker = ScriptWorker('crontick')
    catalog = worker.root.catalog
    address_for_docid = catalog.document_map.address_for_docid
    query = catalog.query
    
    unix_now = timegm(utcnow().timetuple())
    
    #Open polls
    q_str = "start_time <= %s and workflow_state == 'planned' and content_type == 'Poll'" % unix_now
    for id in query(q_str)[1]:
        path = address_for_docid(id)
        obj = find_resource(worker.root, path)
        unrestricted_wf_transition_to(obj, 'ongoing')
        worker.logger.info()
        worker.logger.info("Setting 'ongoing' state poll at: %s" % path)
    
    transaction.commit()
    worker.shutdown()
    