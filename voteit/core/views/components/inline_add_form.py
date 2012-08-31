from betahaus.viewcomponent.decorators import view_action
from pyramid.renderers import render

from voteit.core import VoteITMF as _
from voteit.core.security import ADD_PROPOSAL
from voteit.core.security import ADD_DISCUSSION_POST
from voteit.core.fanstaticlib import voteit_deform



@view_action('proposals', 'add_form', ctype = 'Proposal')
@view_action('discussions', 'add_form', ctype = 'DiscussionPost')
def inline_add_form(context, request, va, **kw):
    """ For agenda item contexts.
    """
    ctype = va.kwargs['ctype']
    api = kw['api']
    if ctype == 'Proposal' and not api.context_has_permission(ADD_PROPOSAL, context):
        msg = api.translate(_(u"no_propose_perm_notice",
                              default = u"You don't have the required permission to add a proposal here"))
        return "<hr/>%s" % msg
    if ctype == 'DiscussionPost' and not api.context_has_permission(ADD_DISCUSSION_POST, context):
        msg = api.translate(_(u"no_discuss_perm_notice",
                              default = u"You don't have the required permission to add a discussion post here"))
        return "<hr/>%s" % msg
    #Important! This widget must register all the needed resources for the form that will be included later!
    voteit_deform.need()
    response = {}
    response['user_image_tag'] = api.user_profile.get_image_tag()
    query = {'content_type': va.kwargs['ctype']}
    tag = request.GET.get('tag', None)
    if tag:
        query['tag'] = tag
    response['url'] = request.resource_url(context, '@@_inline_form', query=query)
    if ctype == 'Proposal':
        response['text'] = _(u'${username} propose', mapping={'username': api.userid})
    else:
        response['text'] = _(u'Add')
    if ctype == 'Proposal':
        return render('../templates/snippets/inline_dummy_proposal_button.pt', response, request = request)
    return render('../templates/snippets/inline_dummy_form.pt', response, request = request)
