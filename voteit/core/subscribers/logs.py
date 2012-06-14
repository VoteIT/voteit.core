from pyramid.events import subscriber
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from repoze.folder.interfaces import IObjectAddedEvent
from repoze.folder.interfaces import IObjectWillBeRemovedEvent

from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.models.interfaces import ILogHandler
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import IVote
from voteit.core.models.interfaces import IMeeting
from voteit.core.interfaces import IWorkflowStateChange
from voteit.core.interfaces import IObjectUpdatedEvent
from voteit.core import VoteITMF as _


def _get_logger_context(obj):
    meeting = find_interface(obj, IMeeting)
    return meeting and meeting or find_root(obj)


@subscriber([IBaseContent, IObjectAddedEvent])
@subscriber([IVote, IObjectAddedEvent])
def log_content_added(obj, event):
    """ Will log all kinds of content added.
        When something is outside of a meeting context, it will be logged to site root. (Like users)
    """
    #Which context to use?
    context = _get_logger_context(obj)
    request = get_current_request()
    log_handler = request.registry.getAdapter(context, ILogHandler)
    userid = authenticated_userid(request)

    msg = _(u"${ctype} was added to ${path}",
            mapping={'ctype': obj.content_type, 'path':resource_path(obj)})
    log_handler.add(obj.uid, msg, tags=('added',), userid=userid)

@subscriber([IBaseContent, IObjectWillBeRemovedEvent])
@subscriber([IVote, IObjectWillBeRemovedEvent])
def log_content_removed(obj, event):
    #Which context to use?
    context = _get_logger_context(obj)
    request = get_current_request()
    log_handler = request.registry.getAdapter(context, ILogHandler)
    userid = authenticated_userid(request)

    msg = _(u"${ctype} removed from ${path}",
            mapping={'ctype': obj.content_type, 'path':resource_path(obj)})
    log_handler.add(obj.uid, msg, tags=('removed',), userid=userid)

@subscriber([IWorkflowAware, IWorkflowStateChange])
def log_wf_state_change(obj, event):
    #Which context to use?
    context = _get_logger_context(obj)
    request = get_current_request()
    log_handler = request.registry.getAdapter(context, ILogHandler)
    userid = authenticated_userid(request)
    msg = _(u"log_ctype_state_change",
            default = u"${ctype} in path ${path} changed state from '${old_state}' to '${new_state}'",
            mapping={'ctype': obj.content_type,
                     'path':resource_path(obj),
                     'old_state':event.old_state,
                     'new_state':event.new_state})
    log_handler.add(obj.uid, msg, tags=('workflow',), userid=userid)

@subscriber([IBaseContent, IObjectUpdatedEvent])
@subscriber([IVote, IObjectUpdatedEvent])
def log_content_updated(obj, event):
    #Abort logging if unread is the only thing changed
    if len(event.indexes) == 1 and 'unread' in event.indexes:
        return
    #Context is either meeting or site root
    context = _get_logger_context(obj)
    request = get_current_request()
    log_handler = request.registry.getAdapter(context, ILogHandler)
    userid = authenticated_userid(request)

    msg = _(u"${ctype} in ${path} updated",
            mapping={'ctype': obj.content_type, 'path':resource_path(obj)})
    log_handler.add(obj.uid, msg, tags=('updated',), userid=userid)
