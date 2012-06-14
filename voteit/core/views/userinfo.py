from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from pyramid.renderers import render_to_response
from pyramid.renderers import render
from pyramid.view import view_config
from pyramid.security import effective_principals
from pyramid.httpexceptions import HTTPForbidden
from webhelpers.html.converters import nl2br
from webhelpers.html.render import sanitize

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IDateTimeUtil
from voteit.core.security import find_authorized_userids
from voteit.core.security import VIEW
from voteit.core.models.catalog import metadata_for_query


USERINFO_TPL = 'templates/snippets/userinfo.pt'


def _strip_and_truncate(text, limit=100):
    text = sanitize(text)
    if len(text) > limit:
        text = "%s<...>" % nl2br(text[:limit])
    return nl2br(text)


@view_config(context=IMeeting, name="_userinfo", permission=VIEW)
def user_info_view(context, request, info_userid=None):
    """ Special view to allow other meeting participants to see information about a user
        who's in the same meeting as them.
    """
    root = find_root(context)

    if info_userid is None:
        info_userid = request.GET.get('userid', None)
    if info_userid is None:
        raise ValueError("No userid specified")

    def _last_entries():
        """ Return last proposals or discussion posts that this user created """
        query = {}
        #context can be user profile too
        if IMeeting.providedBy(context):
            query['path'] = resource_path(context)
        else:
            query['path'] = resource_path(root)
        query['allowed_to_view'] = {'operator':'or', 'query': effective_principals(request)}
        query['creators'] = info_userid
        query['content_type'] = {'query':('Proposal','DiscussionPost'), 'operator':'or'}
        query['sort_index'] = 'created'
        query['reverse'] = True
        query['limit'] = 5
        return metadata_for_query(root.catalog, **query)

    if info_userid in find_authorized_userids(context, (VIEW,)):
        #User is allowed here, so do lookup
        user = root.users.get(info_userid)
    else:
        raise ValueError("No user with that userid found in context")

    dt_util = request.registry.getUtility(IDateTimeUtil)

    response = {}
    response['user'] = user
    response['info_userid'] = info_userid
    response['about_me'] = nl2br(user.get_field_value('about_me'))
    response['last_entries'] = _last_entries()
    response['truncate'] = _strip_and_truncate
    response['relative_time_format'] = dt_util.relative_time_format
    if request.is_xhr:
        return render_to_response(USERINFO_TPL, response, request = request)
    #Since this view should not be called directly in a meeting context,
    #we raise a forbidden if that is the case.
    if IMeeting.providedBy(context):
        raise HTTPForbidden(_(u"Direct access to this is not allowed"))
    return render(USERINFO_TPL, response, request = request)
