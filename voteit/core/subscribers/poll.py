from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request

from voteit.core.models.interfaces import IPoll
from voteit.core.interfaces import IObjectUpdatedEvent


@subscriber([IPoll, IObjectUpdatedEvent])
def change_states_proposals(obj, event):
    """ Change state on proposals when adding them to planed poll. """

    request = get_current_request()
    
    if obj.get_workflow_state() == 'planned':
        for proposal in obj.get_proposal_objects():
            if proposal.get_workflow_state() != 'voting':
                proposal.set_workflow_state(request, 'voting')
