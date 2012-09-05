from pyramid.events import subscriber
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.catalog.query import Eq

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.models.catalog import metadata_for_query


@subscriber([IProposal, IObjectAddedEvent])
def proposal_id(obj, event):
    """ Assign a propsal ID to all proposals when they're added.
    """
    root = find_root(obj)
    meeting = find_interface(obj, IMeeting)
    catalog = root.catalog

    creators = obj.get_field_value('creators')
    if not creators:
        raise ValueError("The object %s doesn't have a creator assigned. Can't generate automatic id." % obj)

    #By convention, first name in list is main creator.
    #No support for many creators yet but it might be implemented.
    creator = creators[0]

    results = metadata_for_query(catalog, creators = creator, content_type = 'Proposal', path = resource_path(meeting))
    current_aid_ints = [x['aid_int'] for x in results if x.get('aid_int')]
    if current_aid_ints:
        aid_int = max(current_aid_ints) + 1
    else:
        aid_int = 1
    aid = "%s-%s" % (creator, aid_int)
    obj.set_field_appstruct({'aid': aid, 'aid_int': aid_int})
