from betahaus.viewcomponent.decorators import view_action
from pyramid.renderers import render

from voteit.core import VoteITMF as _
from voteit.core.security import ADD_PROPOSAL
from voteit.core.security import ADD_DISCUSSION_POST
from voteit.core.fanstaticlib import voteit_deform



@view_action('proposals', 'add_form', permission = ADD_PROPOSAL, ctype = 'Proposal')
@view_action('discussions', 'add_form', permission = ADD_DISCUSSION_POST, ctype = 'DiscussionPost')
def inline_add_form(context, request, va, **kw):
    """ For agenda item contexts.
    """
    #Important! This widget must register all the needed resources for the form that will be included later!
    voteit_deform.need()
    api = kw['api']
    response = {}
    response['user_image_tag'] = api.user_profile.get_image_tag()
    response['url'] = "%s@@_inline_form?content_type=%s" % (api.resource_url(context, request), va.kwargs['ctype'])
    if va.kwargs['ctype'] == 'Proposal':
        response['text'] = _(u'${username} propose', mapping={'username': api.userid})
    else:
        response['text'] = _(u'Add')
    return render('../templates/snippets/inline_dummy_form.pt', response, request = request)
