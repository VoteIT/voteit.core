from pyramid.events import subscriber
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.folder.interfaces import IObjectWillBeRemovedEvent

from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUnreadAware
from voteit.core.interfaces import IWorkflowStateChange


@subscriber([IUnreadAware, IObjectAddedEvent])
@subscriber([IPoll, IWorkflowStateChange])
def mark_unread(obj, event):
    obj.mark_all_unread()

@subscriber([IUser, IObjectWillBeRemovedEvent])
def unread_user_removed(obj, event):
    #FIXME: Do we need this?
    pass

