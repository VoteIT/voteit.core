from arche.models.catalog import quick_reindex
from pyramid.threadlocal import get_current_request
from voteit.core.models.interfaces import IMeeting, IAgendaItem


def _migrate(obj):
    if hasattr(obj, 'state'):
        # Bypass transitions
        obj.workflow.state = obj.state
        delattr(obj, 'state')


def evolve(root):
    """ Move the workflow attribute and reindex those content types
    """
    #self.context.__wf_state__
    request = get_current_request()
    for meeting in root.values():
        if not IMeeting.providedBy(meeting):
            continue
        _migrate(meeting)
        for invite_ticket in meeting.invite_tickets.values():
            _migrate(invite_ticket)
        for ai in meeting.values():
            if not IAgendaItem.providedBy(ai):
                continue
            _migrate(ai)
            for obj in ai.values():
                if getattr(obj, 'type_name', '') in ('Poll', 'Proposal'):
                    _migrate(obj)
    quick_reindex(request, {'wf_state'})
