from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core import VoteITMF as _


@view_action('user_tags', 'like')
def user_tag_like(brain, request, va, **kw):
    """ Special view action for user tag 'like'.
        It requires catalog metadata + expects a brain
        as context, rather than a full object.
    """
    api = kw['api']
    userids = brain['like_userids']
    display_name =  api.translate(_(u"Like"))
    brain_url = "%s%s" % (request.application_url, brain['path'])

    tag = 'like'
    response = dict(
        context_id = brain['uid'],
        tag = tag,
        display_name = display_name,
        get_userinfo_url = api.get_userinfo_url,
        expl_display_name = _(u"like this"),
    )
    if api.userid and api.userid in userids:
        #Current user likes the current context
        response['link_label'] = _(u"Remove ${display_name}",
                                     mapping={'display_name': display_name})
        response['selected'] = True
        do = "0"
        userids = list(userids)
        userids.remove(api.userid)
    else:
        #Current user hasn't selected the current context
        response['link_label'] = display_name
        response['selected'] = False
        do = "1"
    response['toggle_url']= "%s/_set_user_tag?tag=%s&amp;do=%s" % (brain_url, tag, do)
    response['userids'] = userids
    response['has_entries'] = bool(response['selected'] or userids)
    response['tagging_users_url'] =" %s/_tagging_users?tag=%s" % (brain_url, 'like')
    return render('../templates/snippets/user_tag.pt', response, request = request)
