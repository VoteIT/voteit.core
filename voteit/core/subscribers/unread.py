from pyramid.events import subscriber
from pyramid.threadlocal import get_current_registry
from zope.component.event import objectEventNotify

from voteit.core.events import ObjectUpdatedEvent
from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IUnread


@subscriber([IProposal, IWorkflowStateChange])
def clear_unread_from_retracted_proposals(obj, event):
    if obj.get_workflow_state() != 'retracted':
        return
    reg = get_current_registry()
    unread = reg.queryAdapter(obj, IUnread)
    if unread and unread.unread_storage:
        unread.unread_storage.clear()
        objectEventNotify(ObjectUpdatedEvent(obj, indexes = ('unread',), metadata = False))
