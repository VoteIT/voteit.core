#from pyramid.view import view_config

#from voteit.core.models.interfaces import IAgendaItem
#from voteit.core.models.interfaces import IUserUnread
#from voteit.core.security import VIEW


#@view_config(context = IAgendaItem, name = "_mark_read", permission = VIEW, renderer='json')
def mark_content_as_read(context, request):
    """ Mark content as read for user. All uids are stored on the users profile object.
        Any updates that will occur at the same time will likely be able to be resolved
        via ZODBs regular conflict resolution.
    """
    userid = request.authenticated_userid
    if not userid:
        #Simply ignore the call, don't raise any exception
        return {'error': 'unauthorized'}
    user = getattr(request, 'profile', None)
    if not user:
        return {'error': 'no_user'}
    unread = IUserUnread(user)
    removed_items = unread.remove_uids(context, request.POST.getall('read_uids[]'))
    results = set()
    for v in removed_items.values():
        results.update(v)
    return {'marked_read': list(results)}
