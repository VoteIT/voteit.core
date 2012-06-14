from repoze.folder.interfaces import IObjectAddedEvent
from pyramid.events import subscriber
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path

from repoze.catalog.query import Eq

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.catalog import reindex_object


@subscriber([IProposal, IObjectAddedEvent])
def proposal_id(obj, event):
    root = find_root(obj)
    meeting = find_interface(obj, IMeeting)
    catalog = root.catalog
    
    creators = obj.get_field_value('creators')
    if creators:
        creator = creators[0]
        for n in range(1, 500):
            aid = "%s-%s" % (creator, n)
            
            #check that aid is unique in meeting
            count, result = catalog.query(Eq('path', resource_path(meeting)) & \
                                          Eq('aid', aid))
            if count == 0:
                obj.set_field_value('aid', aid)
                reindex_object(root.catalog, obj, indexes=('aid',))
                return
            
        raise KeyError("No automatic id could be generated") 
        