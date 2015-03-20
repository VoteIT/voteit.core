from pyramid.traversal import find_resource
from pyramid.traversal import find_root
from pyramid.view import view_config

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IUnread
from voteit.core.security import VIEW


@view_config(context = IAgendaItem, name = "_mark_read", permission = VIEW, renderer='json')
def mark_content_as_read(context, request):
    """ This view should be called via javascript. Its not ment to return anything,
        but rather to make sure the writes when you mark something as read is performed
        in a separate request. That way it should be a lot less likely for them to fail,
        and even if they do fail it shouldn't have any effect on the current view.
        (Other than the fact that they will still be unread)
        Also, any retry will have to do very little rather than running the full request again.
    """
    userid = request.authenticated_userid
    if not userid:
        #Simply ignore the call, don't raise any exception
        return {'error': 'unauthorized'}
    root = find_root(context)
    catalog = root.catalog
    address_for_docid = root.document_map.address_for_docid
    results = []
    for uid in request.POST.getall('read_uids[]'):
        for docid in catalog.search(uid = uid)[1]:
            path = address_for_docid(docid)
            obj = find_resource(root, path)
            unread = IUnread(obj, None)
            if unread:
                results.append(uid)
                unread.mark_as_read(userid)
    return {'marked_read': results}
