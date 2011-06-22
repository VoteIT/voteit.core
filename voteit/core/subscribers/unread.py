from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.folder.interfaces import IObjectWillBeRemovedEvent
from zope.component import getUtility

from voteit.core import security
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import ISQLSession
from voteit.core.models.unread import Unreads


@subscriber(IMeeting, IObjectAddedEvent)
@subscriber(IAgendaItem, IObjectAddedEvent)
@subscriber(IProposal, IObjectAddedEvent)
@subscriber(IPoll, IObjectAddedEvent)
@subscriber(IDiscussionPost, IObjectAddedEvent)
def unread_content_added(obj, event):
    session = getUtility(ISQLSession)()
    unreads = Unreads(session)
    userids = security.find_authorized_userids(obj, (security.VIEW, ))
    for userid in userids:
        unreads.add(userid, obj.uid)

@subscriber(IUser, IObjectWillBeRemovedEvent)
def unread_user_removed(obj, event):
    session = getUtility(ISQLSession)()
    unreads = Unreads(session)
    unreads.remove_user(obj.__name__)

@subscriber(IMeeting, IObjectWillBeRemovedEvent)
@subscriber(IAgendaItem, IObjectWillBeRemovedEvent)
@subscriber(IProposal, IObjectWillBeRemovedEvent)
@subscriber(IPoll, IObjectWillBeRemovedEvent)
@subscriber(IDiscussionPost, IObjectWillBeRemovedEvent)
def unread_content_removed(obj, event):
    session = getUtility(ISQLSession)()
    unreads = Unreads(session)
    unreads.remove_context(obj.uid)
