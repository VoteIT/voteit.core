from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IMeeting


def evolve(root):
    """ Change the Proposals so title and text are separated.
        Old proposals used to have only a title field that could be really long.
        
        Also add portlets to all meetings.
    """
    from arche.utils import find_all_db_objects
    from arche.portlets import get_portlet_manager
    from voteit.core.models.meeting import add_default_portlets_meeting

    manager = get_portlet_manager(root)
    if not manager.get_portlets('right', 'meeting_list'):
        manager.add('right', 'meeting_list')

    for obj in find_all_db_objects(root):
        if IProposal.providedBy(obj):
            try:
                obj.text = obj.field_storage.pop('title')
            except KeyError:
                pass
        elif IMeeting.providedBy(obj):
            add_default_portlets_meeting(obj)
