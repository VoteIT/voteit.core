from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_interface
from repoze.folder.interfaces import IObjectAddedEvent

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem


@subscriber([IAgendaItem, IObjectAddedEvent])
def set_initial_order(obj, event):
    """ Sets the initial order of the agenda item """
    meeting = find_interface(obj, IMeeting)
    assert meeting
    
    order = 0
    for ai in meeting.values():
        if IAgendaItem.providedBy(ai):
            if ai.get_field_value('order') >= order:
                order = ai.get_field_value('order')+1

    obj.set_field_appstruct({'order': order})