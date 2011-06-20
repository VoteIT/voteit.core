from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid
from pyramid.traversal import find_root
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.folder.interfaces import IObjectWillBeRemovedEvent

from voteit.core import security
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.unread import Unreads

@subscriber(IMeeting, IObjectAddedEvent)
@subscriber(IAgendaItem, IObjectAddedEvent)
@subscriber(IProposal, IObjectAddedEvent)
@subscriber(IPoll, IObjectAddedEvent)
@subscriber(IDiscussionPost, IObjectAddedEvent)
def unread_content_added(obj, event):
    request = get_current_request()
    unreads = Unreads(request)
    root = find_root(obj)
    for userid in root.users.keys():
         if security.ROLE_VIEWER in obj.get_groups(userid):
            unreads.add(userid, obj.uid)

@subscriber(IUser, IObjectWillBeRemovedEvent)
def unread_user_removed(obj, event):
    request = get_current_request()
    unreads = Unreads(request)
    unreads.remove_user(obj.__name__)

@subscriber(IMeeting, IObjectWillBeRemovedEvent)
@subscriber(IAgendaItem, IObjectWillBeRemovedEvent)
@subscriber(IProposal, IObjectWillBeRemovedEvent)
@subscriber(IPoll, IObjectWillBeRemovedEvent)
@subscriber(IDiscussionPost, IObjectWillBeRemovedEvent)
def unread_content_removed(obj, event):
    request = get_current_request()
    unreads = Unreads(request)
    unreads.remove_context(obj.uid)
