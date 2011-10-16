from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request

from voteit.core.models.interfaces import IPoll
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.models.poll import email_voters_about_ongoing_poll


@subscriber([IPoll, IObjectUpdatedEvent])
def change_states_proposals(obj, event):
    """ Change state on proposals when adding them to upcoming poll. """
    request = get_current_request()
    
    if obj.get_workflow_state() == 'upcoming':
        for proposal in obj.get_proposal_objects():
            if proposal.get_workflow_state() != 'voting':
                proposal.set_workflow_state(request, 'voting')

@subscriber([IPoll, IWorkflowStateChange])
def email_voters_about_ongoing_poll_subscriber(obj, event):
    if event.new_state != 'ongoing':
        return
    email_voters_about_ongoing_poll(obj)
