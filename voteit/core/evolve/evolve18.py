from voteit.core.models.interfaces import IMeeting


def evolve(root):
    """ Swap the existing Agenda portets for the fixed agenda portlet type.
    """
    from arche.portlets import get_portlet_manager
    for obj in root.values():
        if IMeeting.providedBy(obj):
            manager = get_portlet_manager(obj)
            for portlet in manager.get_portlets('left', 'agenda'):
                manager.remove('left', portlet.uid)
            if not manager.get_portlets('left_fixed', 'agenda_fixed'):
                manager.add('left_fixed', 'agenda_fixed')
