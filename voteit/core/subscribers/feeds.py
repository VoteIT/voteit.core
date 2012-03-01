from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.folder.interfaces import IObjectWillBeRemovedEvent
from pyramid.url import resource_url

from voteit.core.models.interfaces import IFeedHandler
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core import VoteITMF as _


@subscriber([IDiscussionPost, IObjectAddedEvent])
def feed_discussion_post_added(obj, event):
    """ Will add a feed entry when a discussion post is added if agenda item is not private.
    """
    request = get_current_request()
    userid = authenticated_userid(request)

    agenda_item = find_interface(obj, IAgendaItem)
    if agenda_item.get_workflow_state() == 'private':
        return

    msg = _(u"${userid} has written a post in ${agenda_item}.",
            mapping={'userid': userid, 'agenda_item':agenda_item.title})
    
    url = resource_url(agenda_item, request)
    guid = resource_url(obj, request)

    meeting = find_interface(obj, IMeeting)    
    feed_handler = request.registry.getAdapter(meeting, IFeedHandler)

    feed_handler.add(obj.uid, msg, tags=('discussion_post', 'added',), url=url, guid=guid)
    
@subscriber([IProposal, IObjectAddedEvent])
def feed_proposal_added(obj, event):
    """ Will add a feed entry when a proposal is added if agenda item is not private
    """
    request = get_current_request()
    userid = authenticated_userid(request)

    agenda_item = find_interface(obj, IAgendaItem)
    if agenda_item.get_workflow_state() == 'private':
        return

    msg = _(u"${userid} has made a proposal in ${agenda_item}.",
            mapping={'userid': userid, 'agenda_item':agenda_item.title})
    
    url = resource_url(agenda_item, request)
    guid = resource_url(obj, request)

    meeting = find_interface(obj, IMeeting)    
    feed_handler = request.registry.getAdapter(meeting, IFeedHandler)

    feed_handler.add(obj.uid, msg, tags=('proposal', 'added',), url=url, guid=guid)

@subscriber([IPoll, IWorkflowStateChange])
def feed_poll_state_change(obj, event):
    """ Will add a feed entry when a poll is opened and closes
    """
    if event.new_state in ('ongoing', 'closed'):
    
        request = get_current_request()
        userid = authenticated_userid(request)
    
        agenda_item = find_interface(obj, IAgendaItem)
    
        if event.new_state == 'ongoing': 
            msg = _(u"A poll has started in ${agenda_item}, vote now!",
                    mapping={'userid': userid, 'agenda_item':agenda_item.title})
        elif event.new_state == 'closed':
            msg = _(u"The result of a poll in ${agenda_item} is set.",
                    mapping={'agenda_item':agenda_item.title})
    
        url = resource_url(agenda_item, request)
        guid = resource_url(obj, request)
    
        meeting = find_interface(obj, IMeeting)    
        feed_handler = request.registry.getAdapter(meeting, IFeedHandler)
    
        feed_handler.add(obj.uid, msg, tags=('poll', event.new_state,), url=url, guid=guid)

@subscriber([IAgendaItem, IWorkflowStateChange])
def feed_agenda_item_state_change(obj, event):
    """ Will add a feed entry when the state change on agenda items.
    """
    request = get_current_request()
    userid = authenticated_userid(request)

    msg = None
    if event.old_state == 'private' and event.new_state == 'upcoming':
        msg = _(u"${agenda_item} has been added to the agenda.",
            mapping={'agenda_item':obj.title})
    elif event.new_state == 'ongoing':
        msg = _(u"${agenda_item} has been set to ongoing.",
            mapping={'agenda_item':obj.title})
    elif event.new_state == 'closed':
        msg = _(u"${agenda_item} has been closed.",
            mapping={'agenda_item':obj.title})

    if msg:    
        url = resource_url(obj, request)
        guid = url
    
        meeting = find_interface(obj, IMeeting)    
        feed_handler = request.registry.getAdapter(meeting, IFeedHandler)

        feed_handler.add(obj.uid, msg, tags=('agenda_item', event.new_state,), url=url, guid=guid)