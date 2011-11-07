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
    #Note: It's not possible to have nested translation strings. So we do the translation here in advance.
    display_name =  api.translate(_(u"Like"))
    expl_display_name = _(u"like this")
    brain_url = "%s%s" % (request.application_url, brain['path'])
    
    response = dict(
        context_id = brain['uid'],
        toggle_url = "%s/_set_user_tag" % brain_url,
        tag = 'like',
        display_name = display_name,
        get_userinfo_url = api.get_userinfo_url,
        expl_display_name = expl_display_name,
    )
    
    if api.userid and api.userid in userids:
        #Current user likes the current context
        response['button_label'] = _(u"Remove ${display_name}",
                                     mapping={'display_name': display_name})
        response['selected'] = True
        response['do'] = "0"
        userids = list(userids)
        userids.remove(api.userid)
    else:
        #Current user hasn't selected the current context
        response['button_label'] = display_name
        response['selected'] = False
        response['do'] = "1"

    response['userids'] = userids
    response['has_entries'] = bool(response['selected'] or userids)
    response['tagging_users_url'] =" %s/_tagging_users?tag=%s&display_name=%s&expl_display_name=%s" % (brain_url, 'like', display_name, expl_display_name)

    return render('../templates/snippets/user_tag.pt', response, request = request)
