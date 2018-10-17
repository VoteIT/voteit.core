from arche.interfaces import IWorkflowAfterTransition
from pyramid.threadlocal import get_current_request
from repoze.folder.interfaces import IObjectWillBeRemovedEvent

from voteit.core import _
from voteit.core.security import ROLE_VOTER
from voteit.core.security import find_role_userids
from voteit.core.models.interfaces import IPoll
from voteit.core.models.poll import email_voters_about_ongoing_poll


def email_voters_about_ongoing_poll_subscriber(obj, event):
   if event.to_state != 'ongoing':
       return
   # This method will check poll_notification_setting to determine if mail should be sent
   email_voters_about_ongoing_poll(obj)


def save_voters_userids(poll, event):
    if event.to_state == 'ongoing':
        poll.voters_mark_ongoing = find_role_userids(poll, ROLE_VOTER)
    if event.to_state == 'closed':
        poll.voters_mark_closed = find_role_userids(poll, ROLE_VOTER)
        #FIXME: Add vote information if there are votes from users who don't have vote permission currently.
        #That must be regarded as fishy :)


def poll_is_deleted(obj, event):
    """ Set proposals as published when a poll is deleted. Only do this if they're locked for vote."""
    request = get_current_request()
    for proposal in obj.get_proposal_objects():
        if proposal.wf_state == 'voting':
            proposal.workflow.do_transition('published', request)


def includeme(config):
    config.add_subscriber(email_voters_about_ongoing_poll_subscriber, [IPoll, IWorkflowAfterTransition])
    config.add_subscriber(save_voters_userids, [IPoll, IWorkflowAfterTransition])
    config.add_subscriber(poll_is_deleted, [IPoll, IObjectWillBeRemovedEvent])
