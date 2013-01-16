from pyramid.events import subscriber
from pyramid.threadlocal import get_current_registry
from pyramid.traversal import find_interface
from repoze.folder.interfaces import IObjectAddedEvent

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IProposalIds


@subscriber([IProposal, IObjectAddedEvent])
def create_proposal_id(obj, event):
    """ Assign a propsal ID to all proposals when they're added,
        unless they already have an id.
    """
    #FIXME The code here should be in the adapter
    if obj.get_field_value('aid') and obj.get_field_value('aid_int'):
        return
    meeting = find_interface(obj, IMeeting)
    registry = get_current_registry()
    creators = obj.get_field_value('creators')
    if not creators:
        raise ValueError("The object %s doesn't have a creator assigned. Can't generate automatic id." % obj)
    #By convention, first name in list is main creator.
    #No support for many creators yet but it might be implemented.
    creator = creators[0]
    proposal_ids = registry.queryAdapter(meeting, IProposalIds)
    aid_int = proposal_ids.get(creator)
    if not aid_int:
        aid_int = 0
    aid_int = aid_int+1
    aid = "%s-%s" % (creator, aid_int)
    obj.set_field_appstruct({'aid': aid, 'aid_int': aid_int})
    proposal_ids.add(creator, aid_int)
