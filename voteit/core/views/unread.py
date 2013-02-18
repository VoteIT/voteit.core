from pyramid.view import view_config
from pyramid.traversal import find_root
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.security import authenticated_userid

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IUnread


@view_config(context = IAgendaItem, name = "_mark_read", permission = NO_PERMISSION_REQUIRED, renderer='json')
def mark_content_as_read(context, request):
    """ This view should be called via javascript. Its not ment to return anything,
        but rather to make sure the writes when you mark something as read is performed
        in a separate request. That way it should be a lot less likely for them to fail,
        and even if they do fail it shouldn't have any effect on the current view.
        (Other than the fact that they will still be unread)
        Also, any retry will have to do very little rather than running the full request again.
    """
    userid = authenticated_userid(request)
    if not userid:
        #Simply ignore the call, don't raise any exception
        return {'error': 'unauthorized'}

    root = find_root(context)
    catalog = root.catalog
    i = 0
    names = request.params.getall(u'unread[]')
    for name in names:
        i += 1
        obj = context.get(name, None)
        if not obj:
            continue
        unread = request.registry.queryAdapter(obj, IUnread)
        if not unread:
            continue
        unread.mark_as_read(userid)

    return {'marked_read': i}
