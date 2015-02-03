from betahaus.viewcomponent import view_action
from betahaus.viewcomponent.interfaces import IViewGroup
from pyramid.renderers import render
from pyramid.traversal import find_resource
from pyramid.traversal import find_interface

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IAgendaItem, IProposal,\
    IDiscussionPost
from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.security import RETRACT 
from voteit.core.security import VIEW
from voteit.core.security import ADD_PROPOSAL
from voteit.core.security import ADD_DISCUSSION_POST
from voteit.core.security import DELETE


# @view_action('main', 'metadata_listing', permission=VIEW)
# def metadata_listing(context, request, va, **kw):
#     """ This is the main renderer for post meta.
#         It will call all view components in the group metadata_listing.
#         In turn, some of those will call other groups.
#     """
#     util = request.registry.getUtility(IViewGroup, name='metadata_listing')
#     response = {'view_actions': util.values(), 'va_kwargs': kw,}
#     return render('templates/metadata/metadata_listing.pt', response, request = request)

@view_action('metadata_listing', 'state', permission=VIEW, interface = IWorkflowAware)
def meta_state(context, request, va, **kw):
    state_id = context.get_workflow_state()
    state_info = context.workflow.state_info(None, request)
    translated_state_title = state_id
    for info in state_info:
        if info['name'] == state_id:
            ts = _
            translated_state_title = request.localizer.translate(ts(info['title']))
            break
    return '<span class="%s icon iconpadding">%s</span>' % (state_id, translated_state_title)

@view_action('metadata_listing', 'time', permission=VIEW)
def meta_time(context, request, va, **kw):
    #api = kw['api']
    #brain = kw['brain']
    #return '<span class="time">%s</span>' % api.translate(api.dt_util.relative_time_format(brain['created']))
    return '<span class="time">%s</span>' % request.localizer.translate(request.dt_handler.format_relative(context.created))

@view_action('metadata_listing', 'retract', permission=VIEW, interface = IWorkflowAware)
def meta_retract(context, request, va, **kw):
    if context.get_workflow_state() != 'published':
        return
    if not request.authenticated_userid in context.creators:
        return
    #Now for the 'expensive' stuff
    ai = find_interface(context, IAgendaItem)
    if not request.has_permission(ADD_PROPOSAL, ai) and request.has_permission(RETRACT, context):
        return
    url = request.resource_url(context, 'state', query = {'state': 'retracted'})
    return '<a class="retract confirm-retract" href="%s">%s</a>' % (url, request.localizer.translate(_(u'Retract')))

@view_action('metadata_listing', 'user_tags', permission=VIEW)
def meta_user_tags(context, request, va, **kw):
    return
    brain = kw['brain']
    api = kw['api']
    del kw['brain'] #So we don't pass it along as well, causing an argument conflict
    return api.render_view_group(brain, request, 'user_tags', **kw)

@view_action('metadata_listing', 'answer', permission=VIEW)
def meta_answer(context, request, va, **kw):
    """ Create a reply link. Replies are always discussion posts. Brain here is a metadata object
        of the content that's being replied to.
    """
    return
    api = kw['api']
    brain = kw['brain']
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

@view_action('metadata_listing', 'edit', title = _(u"Edit"))
def edit_action(context, request, va, **kw):
    return
    api = kw['api']
    if api.show_moderator_actions:
        brain = kw['brain']
        return '<a href="%s%s/edit">%s</a>'  %\
            (request.application_url, brain['path'], api.translate(va.title))

@view_action('metadata_listing', 'tag', permission=VIEW, interface = IProposal)
def meta_tag(context, request, va, **kw):
    aid = context.aid
    return '<span><a class="tag" ' \
           'href="?tag=%s" ' \
           '>#%s</a> </span>' % (aid, aid)

@view_action('metadata_listing', 'delete', permission = DELETE,interface = IDiscussionPost)
def meta_delete(context, request, va, **kw):
    return u'<span><a class="delete" href="%s">%s</a></span>' % (request.resource_url(context, 'delete'), request.localizer.translate(_("Delete")))
