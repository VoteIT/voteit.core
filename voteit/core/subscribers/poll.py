from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.folder.interfaces import IObjectWillBeRemovedEvent
from repoze.workflow.workflow import WorkflowError
from pyramid.exceptions import HTTPForbidden

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IPoll
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.models.poll import email_voters_about_ongoing_poll


@subscriber([IPoll, IWorkflowStateChange])
def change_states_proposals(obj, event):
    """ Change state on proposals when adding them to upcoming poll. """
    request = get_current_request()
    if obj.get_workflow_state() == 'upcoming':
        for proposal in obj.get_proposal_objects():
            if proposal.get_workflow_state() != 'voting':
                try:
                    proposal.set_workflow_state(request, 'voting')
                except WorkflowError:
                    raise HTTPForbidden(_(u"workflow_error_when_setting_proposal_as_voting",
                                          default = u"Can't set Proposal '${title}' as 'Locked for voting'. It's probably not in the state published, or has already been handled in another way. All changes aborted, please check the proposals and try again.",
                                          mapping = {'title': obj.title}))

@subscriber([IPoll, IWorkflowStateChange])
def email_voters_about_ongoing_poll_subscriber(obj, event):
    if event.new_state != 'ongoing':
        return
    #This method will check poll_notification_setting to determine if mail should be sent
    email_voters_about_ongoing_poll(obj)

@subscriber([IPoll, IObjectAddedEvent])
@subscriber([IPoll, IObjectUpdatedEvent])
def create_reject_proposal(obj, event):
    """ Adding a reject proposal to poll. This is a subscriber because
        poll needs to be added to the agenda_item for this to work """
    obj.create_reject_proposal()

@subscriber([IPoll, IObjectWillBeRemovedEvent])
def poll_is_deleted(obj, event):
    """ Set proposals as published when a poll is deleted. Only do this if they're locked for vote."""
    request = get_current_request()
    for proposal in obj.get_proposal_objects():
        if proposal.get_workflow_state() == 'voting':
            proposal.set_workflow_state(request, 'published')
