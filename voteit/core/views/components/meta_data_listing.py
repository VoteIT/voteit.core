from betahaus.viewcomponent import view_action
from betahaus.viewcomponent.interfaces import IViewGroup
from pyramid.renderers import render
from pyramid.traversal import find_resource
from pyramid.traversal import find_interface

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.models.discussion_post import DiscussionPost
from voteit.core.models.proposal import Proposal
from voteit.core.security import RETRACT 
from voteit.core.security import VIEW



@view_action('main', 'meta_data_listing', permission=VIEW)
def meta_data_listing(context, request, va, **kw):
    """ This is the main renderer for post meta.
        It will call all view components in the group meta_data_listing.
        In turn, some of those will call other groups.
    """   
    api = kw['api']
    util = request.registry.getUtility(IViewGroup, name='meta_data_listing')
    view_actions = []
    for _va in util.get_context_vas(context, request):
        output = _va(context, request, **kw)
        if output:
            view_actions.append(output)
    
    response = {'view_actions': view_actions,}
    return render('../templates/snippets/meta_data_listing.pt', response, request = request)


@view_action('meta_data_listing', 'state', permission=VIEW)
def meta_state(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']
    
    obj = find_resource(api.root, brain['path'])
    if not IWorkflowAware.providedBy(obj):
        return ''
    
    state_id = brain['workflow_state']
    state_info = _dummy[brain['content_type']].workflow.state_info(None, request)
    
    translated_state_title = state_id
    for info in state_info:
        if info['name'] == state_id:
            translated_state_title = api.translate(api.tstring(info['title']))

    return '<span class="%s icon iconpadding">%s</span>' % (state_id, translated_state_title)

@view_action('meta_data_listing', 'time', permission=VIEW)
def meta_time(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']

    return '<span class="time">%s</span>' % api.translate(api.dt_util.relative_time_format(brain['created']))

@view_action('meta_data_listing', 'retract', permission=VIEW)
def meta_retract(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']
    
    if brain['workflow_state'] != 'published':
        return ''
    if not api.userid in brain['creators']:
        return ''
    #Now for the 'expensive' stuff
    obj = find_resource(api.root, brain['path'])
    if not api.context_has_permission(RETRACT, obj):
        return ''
        
    return '<a class="retract confirm-retract" ' \
           'href="%s%s/state?state=retracted" ' \
           '>%s</a>' % (request.application_url, brain['path'], api.translate(_(u'Retract')))
           
@view_action('meta_data_listing', 'user_tags', permission=VIEW)
def meta_user_tags(context, request, va, **kw): 
    brain = kw['brain']
    del kw['brain']
    
    util = request.registry.getUtility(IViewGroup, name='user_tags')
    tags = []
    for _va in util.get_context_vas(context, request):
            tags.append(_va(brain, request, **kw))
    
    response = {'tags': tags,}
    return render('../templates/snippets/meta_data_listing_user_tags.pt', response, request = request)


@view_action('meta_data_listing', 'answer', permission=VIEW)
def meta_answer(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']
    if not api.meeting.get_field_value('tags_enabled', True) or \
        api.context.get_field_value('discussion_block', False):
        return u""
    #Check add permission
    ai = find_interface(context, IAgendaItem)
    add_perm = api.content_types_add_perm('Proposal')
    if not api.context_has_permission(add_perm, ai):
        return u""

    if brain['content_type'] == 'Proposal':
        label = _(u'Comment')
    else:
        label = _(u'Reply')
                  
    return '<a class="answer" ' \
           'href="%s%s/answer" ' \
           '>%s</a>'  % (request.application_url, brain['path'], api.translate(label))

@view_action('meta_data_listing', 'tag', permission=VIEW)
def meta_tag(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']
    
    if not brain['content_type'] == 'Proposal':
        return ''

    return '<a class="tag" ' \
           'href="?tag=%s" ' \
           '>#%s</a>' % (brain['aid'], brain['aid'])

_dummy = {'Proposal': Proposal(),
          'DiscussionPost': DiscussionPost()}
