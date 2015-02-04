from betahaus.viewcomponent.decorators import view_action
from betahaus.pyracont.factories import createSchema
from pyramid.renderers import render

from voteit.core import VoteITMF as _
from voteit.core.security import ADD_PROPOSAL
from voteit.core.security import ADD_DISCUSSION_POST
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.views.agenda_item import inline_add_form
#from voteit.core.fanstaticlib import jquery_form

#@view_action('proposals', 'add_form', interface = IAgendaItem)
def inline_add_proposal_form(context, request, va, **kw):
    """ For agenda item contexts.
    """
    api = kw['api']
    #jquery_form.need() #This isn't included in widgets for some reason
    form = inline_add_form(api, 'Proposal', {})
    api.register_form_resources(form)
    if not api.context_has_permission(ADD_PROPOSAL, context):
        if context.get_workflow_state() == 'closed':
            msg = api.translate(_(u"no_propose_ai_closed",
                                  default = u"The agenda item is closed, you can't add a proposal here"))
        elif api.meeting.get_workflow_state() == 'closed':
            msg = api.translate(_(u"no_propose_meeting_closed",
                                  default = u"The meeting is closed, you can't add a proposal here"))
        else:
            msg = api.translate(_(u"no_propose_perm_notice",
                                  default = u"You don't have the required permission to add a proposal here"))
        return "<hr/>%s" % msg
    response = {}
    query = {'content_type': 'Proposal'}
    tag = request.GET.get('tag', None)
    if tag:
        query['tag'] = tag
    response['url'] = request.resource_url(context, '_inline_form', query = query)
    response['text'] = _(u'${username} propose', mapping={'username': api.userid})
    return render('../templates/snippets/inline_dummy_proposal_button.pt', response, request = request)

@view_action('discussions', 'add_form', interface = IAgendaItem)
def inline_add_discussion_form(context, request, va, **kw):
    """ For agenda item contexts.
    """
    api = kw['api']
    jquery_form.need() #This isn't included in widgets for some reason
    form = inline_add_form(api, 'DiscussionPost', {})
    api.register_form_resources(form)
    if not api.context_has_permission(ADD_DISCUSSION_POST, context):
        if api.meeting.get_workflow_state() == 'closed':
            msg = api.translate(_(u"no_discuss_meeting_closed",
                                  default = u"The meeting is closed, you can't add a discussion post here"))
        else:
            msg = api.translate(_(u"no_discuss_perm_notice",
                                  default = u"You don't have the required permission to add a discussion post here"))
        return "<hr/>%s" % msg
    response = {}
    response['user_image_tag'] = api.user_profile.get_image_tag(request = request)
    query = {'content_type': 'DiscussionPost'}
    tag = request.GET.get('tag', None)
    if tag:
        query['tag'] = tag
    response['url'] = request.resource_url(context, '_inline_form', query=query)
    response['text'] = _(u'Add')
    return render('../templates/snippets/inline_dummy_form.pt', response, request = request)
