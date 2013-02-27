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
from voteit.core.security import ADD_PROPOSAL
from voteit.core.security import ADD_DISCUSSION_POST
from voteit.core.security import DELETE


@view_action('main', 'metadata_listing', permission=VIEW)
def metadata_listing(context, request, va, **kw):
    """ This is the main renderer for post meta.
        It will call all view components in the group metadata_listing.
        In turn, some of those will call other groups.
    """
    util = request.registry.getUtility(IViewGroup, name='metadata_listing')
    response = {'view_actions': util.get_context_vas(context, request), 'va_kwargs': kw,}
    return render('templates/metadata/metadata_listing.pt', response, request = request)

@view_action('metadata_listing', 'state', permission=VIEW)
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

@view_action('metadata_listing', 'time', permission=VIEW)
def meta_time(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']

    return '<span class="time">%s</span>' % api.translate(api.dt_util.relative_time_format(brain['created']))

@view_action('metadata_listing', 'retract', permission=VIEW)
def meta_retract(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']
    
    if brain['workflow_state'] != 'published':
        return ''
    if not api.userid in brain['creators']:
        return ''
    #Now for the 'expensive' stuff
    obj = find_resource(api.root, brain['path'])
    ai = find_interface(context, IAgendaItem)
    if not api.context_has_permission(ADD_PROPOSAL, ai) and api.context_has_permission(RETRACT, obj):
        return ''
        
    return '<a class="retract confirm-retract" ' \
           'href="%s%s/state?state=retracted" ' \
           '>%s</a>' % (request.application_url, brain['path'], api.translate(_(u'Retract')))

@view_action('metadata_listing', 'user_tags', permission=VIEW)
def meta_user_tags(context, request, va, **kw):
    brain = kw['brain']
    api = kw['api']
    del kw['brain'] #So we don't pass it along as well, causing an argument conflict
    return api.render_view_group(brain, request, 'user_tags', **kw)

@view_action('metadata_listing', 'answer', permission=VIEW)
def meta_answer(context, request, va, **kw):
    """ Create a reply link. Replies are always discussion posts. Brain here is a metadata object
        of the content that's being replied to.
    """
    api = kw['api']
    brain = kw['brain']
#    if not api.meeting.get_field_value('tags_enabled', True) or \
#        api.context.get_field_value('discussion_block', False):
#        return u""
    #Check add permission
    ai = find_interface(context, IAgendaItem)
    if not api.context_has_permission(ADD_DISCUSSION_POST, ai):
        return u""
    if brain['content_type'] == 'Proposal':
        label = _(u'Comment')
    else:
        label = _(u'Reply')
    return '<a class="answer" href="%s%s/answer">%s</a>'  %\
        (request.application_url, brain['path'], api.translate(label))

@view_action('metadata_listing', 'tag', permission=VIEW)
def meta_tag(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']
    
    if not brain['content_type'] == 'Proposal':
        return u''

    return '<span><a class="tag" ' \
           'href="?tag=%s" ' \
           '>#%s</a> (%s) </span>' % (brain['aid'], brain['aid'], api.get_tag_count(brain['aid']))

@view_action('metadata_listing', 'delete')
def meta_delete(context, request, va, **kw):
    api = kw['api']
    brain = kw['brain']
    if not brain['content_type'] == 'DiscussionPost' and api.userid not in brain['creators']:
        return u''
    obj = find_resource(api.root, brain['path'])
    if not api.context_has_permission(DELETE, obj):
        return u''
    return u'<span><a class="delete" href="%s">%s</a></span>' % (request.resource_url(obj, 'delete'), api.translate(_(u"Delete")))

_dummy = {'Proposal': Proposal(),
          'DiscussionPost': DiscussionPost()}
