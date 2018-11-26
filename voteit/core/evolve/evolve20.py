from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting


def evolve(root):
    """ Remove old redis attrs
    """
    for meeting in [x for x in root.values() if IMeeting.providedBy(x)]:
        if hasattr(meeting, '_read_names_counter'):
            delattr(meeting, '_read_names_counter')
        for ai in [x for x in meeting.values() if IAgendaItem.providedBy(x)]:
            if hasattr(ai, '_read_names'):
                delattr(ai, '_read_names')
