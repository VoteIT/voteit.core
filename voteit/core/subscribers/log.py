from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid
from pyramid.traversal import find_interface
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.folder.interfaces import IObjectWillBeRemovedEvent

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IProposal
from voteit.core.models.log import Logs
from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.interfaces import IObjectUpdatedEvent

@subscriber(IMeeting, IObjectAddedEvent)
def log_meeting_added(obj, event):
    #Log entry
    request = get_current_request()
    userid = authenticated_userid(request)
    logs = Logs(request)
    logs.add(
        obj.uid, 
        '%s %s added' % (obj.content_type, obj.title), 
        tags='added', 
        userid=userid, 
        primaryuid=obj.uid,
    )
    
@subscriber(IAgendaItem, IObjectAddedEvent)
@subscriber(IProposal, IObjectAddedEvent)
def log_content_added(obj, event):
    #Log entry
    request = get_current_request()
    meeting = find_interface(obj, IMeeting)
    userid = authenticated_userid(request)
    logs = Logs(request)
    logs.add(
        meeting.uid, 
        '%s %s added' % (obj.content_type, obj.title), 
        tags='added', 
        userid=userid, 
        primaryuid=obj.uid,
    )
    
@subscriber(IPoll, IObjectAddedEvent)
def log_poll_added(obj, event):
    #Log entry
    request = get_current_request()
    meeting = find_interface(obj, IMeeting)
    userid = authenticated_userid(request)
    logs = Logs(request)
    logs.add(
        meeting.uid, 
        '%s %s added' % (obj.content_type, obj.title), 
        tags='added', 
        userid=userid, 
        primaryuid=obj.uid,
    )
    for proposal in obj.get_proposal_objects():
        logs.add(
            meeting.uid, 
            '%s %s added to %s %s ' % (proposal.content_type, proposal.title, obj.content_type, obj.title), 
            tags='proposal to poll', 
            userid=userid, 
            primaryuid=obj.uid,
            secondaryuid=proposal.uid,
        )
    
@subscriber(IMeeting, IObjectWillBeRemovedEvent)
@subscriber(IAgendaItem, IObjectWillBeRemovedEvent)
@subscriber(IProposal, IObjectWillBeRemovedEvent)
@subscriber(IPoll, IObjectWillBeRemovedEvent)
def log_content_deleted(obj, event):
    #Log entry
    request = get_current_request()
    meeting = find_interface(obj, IMeeting)
    userid = authenticated_userid(request)
    logs = Logs(request)
    logs.add(
        meeting.uid, 
        '%s %s deleted' % (obj.content_type, obj.title), 
        tags='deleted', 
        userid=userid, 
        primaryuid=obj.uid,
    )
    
    
@subscriber(IMeeting, IWorkflowStateChange)
@subscriber(IAgendaItem, IWorkflowStateChange)
@subscriber(IProposal, IWorkflowStateChange)
@subscriber(IPoll, IWorkflowStateChange)
def log_state_changed(obj, event):
    request = get_current_request()
    meeting = find_interface(obj, IMeeting)
    userid = authenticated_userid(request)
    logs = Logs(request)
    logs.add(
        meeting.uid, 
        'changed state from %s to %s on %s %s' % (event.old_state, event.new_state, obj.content_type, obj.title), 
        tags='state changed', 
        userid=userid, 
        primaryuid=obj.uid,
    )
    
@subscriber(IMeeting, IObjectUpdatedEvent)
@subscriber(IAgendaItem, IObjectUpdatedEvent)
@subscriber(IProposal, IObjectUpdatedEvent)
@subscriber(IPoll, IObjectUpdatedEvent)
def log_content_updated(obj, event):
    #Log entry
    request = get_current_request()
    meeting = find_interface(obj, IMeeting)
    userid = authenticated_userid(request)
    logs = Logs(request)
    logs.add(
        meeting.uid, 
        '%s %s updated' % (obj.content_type, obj.title), 
        tags='updated', 
        userid=userid, 
        primaryuid=obj.uid,
    )
