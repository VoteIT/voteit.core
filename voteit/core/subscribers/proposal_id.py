from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.catalog.query import Eq

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IProposalIds
from voteit.core.models.catalog import metadata_for_query


def create_proposal_id(obj):
    root = find_root(obj)
    meeting = find_interface(obj, IMeeting)
    request = get_current_request()
    catalog = root.catalog
    creators = obj.get_field_value('creators')
    if not creators:
        raise ValueError("The object %s doesn't have a creator assigned. Can't generate automatic id." % obj)

    #By convention, first name in list is main creator.
    #No support for many creators yet but it might be implemented.
    creator = creators[0]

    proposal_ids = request.registry.queryAdapter(meeting, IProposalIds)
    aid_int = proposal_ids.get(creator)
    if not aid_int:
        aid_int = 0
    aid_int = aid_int+1
    aid = "%s-%s" % (creator, aid_int)
    obj.set_field_appstruct({'aid': aid, 'aid_int': aid_int})
    
    proposal_ids.add(creator, aid_int)


@subscriber([IProposal, IObjectAddedEvent])
def proposal_id(obj, event):
    """ Assign a propsal ID to all proposals when they're added.
    """
    create_proposal_id(obj)
