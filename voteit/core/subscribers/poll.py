from pyramid.events import subscriber
from pyramid.exceptions import HTTPForbidden
from pyramid.threadlocal import get_current_request
from repoze.folder.interfaces import IObjectWillBeRemovedEvent
from repoze.workflow.workflow import WorkflowError

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.models.interfaces import IPoll
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

@subscriber([IPoll, IWorkflowStateChange])
def save_voters_userids(obj, event):
    if event.new_state == 'ongoing':
        obj.set_field_value('voters_mark_ongoing', security.find_role_userids(obj, security.ROLE_VOTER))
    if event.new_state == 'closed':
        obj.set_field_value('voters_mark_closed', security.find_role_userids(obj, security.ROLE_VOTER))
        #FIXME: Add vote information if there are votes from users who don't have vote permission currently.
        #That must be regarded as fishy :)

@subscriber([IPoll, IObjectWillBeRemovedEvent])
def poll_is_deleted(obj, event):
    """ Set proposals as published when a poll is deleted. Only do this if they're locked for vote."""
    request = get_current_request()
    for proposal in obj.get_proposal_objects():
        if proposal.get_workflow_state() == 'voting':
            proposal.set_workflow_state(request, 'published')
