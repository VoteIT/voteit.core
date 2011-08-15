import transaction
from calendar import timegm

from pyramid.traversal import find_resource

from voteit.core.scripts.worker import ScriptWorker
from voteit.core.models.date_time_util import utcnow
from voteit.core.security import unrestricted_wf_transition_to


def crontick():
    #FIXME: Needs to be very defensive and handle exceptions
    #FIXME: Needs to log somewhere, perhaps so administrators can read the log online
    
    worker = ScriptWorker('crontick')
    catalog = worker.root.catalog
    address_for_docid = catalog.document_map.address_for_docid
    query = catalog.query
    
    def _resolve_obj(id):
        path = address_for_docid(id)
        return find_resource(worker.root, path)
    
    unix_now = timegm(utcnow().timetuple())
    
    #Open polls
    q_str = "start_time <= %s and workflow_state == 'planned' and content_type == 'Poll'" % unix_now
    for id in query(q_str)[1]:
        obj = _resolve_obj(id)
        unrestricted_wf_transition_to(obj, 'ongoing')
        print "setting ongoing for %s" % obj
    
    transaction.commit()
    worker.shutdown()
    