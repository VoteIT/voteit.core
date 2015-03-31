from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import find_interface

from voteit.core import _
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IWorkflowAware
from voteit.core.security import ADD_DISCUSSION_POST
from voteit.core.security import ADD_PROPOSAL
from voteit.core.security import DELETE
from voteit.core.security import RETRACT 
from voteit.core.security import VIEW


@view_action('metadata_listing', 'state',
             permission = VIEW,
             interface = IWorkflowAware,
             renderer = "voteit.core:templates/snippets/inline_workflow.pt",
             priority = 10)
def meta_state(context, request, va, **kw):
    """ Note: moderator actions also uses this one.
    """
    tstring = _
    response = dict(
        section_title = va.title,
        state_id  = context.get_workflow_state(),
        state_title = tstring(context.current_state_title(request)), #Picked up by translation mechanism in zcml
        states = context.get_available_workflow_states(request),
        context = context,
        tstring = tstring,
    )
    return render(va.kwargs['renderer'], response, request = request)

@view_action('metadata_listing', 'retract', permission=VIEW, interface = IWorkflowAware)
def meta_retract(context, request, va, **kw):
    if request.is_moderator:
        return
    if context.get_workflow_state() != 'published':
        return
    if not request.authenticated_userid in context.creators:
        return
    #Now for the 'expensive' stuff
    ai = find_interface(context, IAgendaItem)
    if not request.has_permission(ADD_PROPOSAL, ai) and request.has_permission(RETRACT, context):
        return
    url = request.resource_url(context, 'state', query = {'state': 'retracted'})
    return '<button type="button" class="btn btn-default btn-xs" href="%s"><span class="text-warning">%s</span></button> ' % \
        (url, request.localizer.translate(_(u'Retract')))

# @view_action('metadata_listing', 'user_tags', permission=VIEW)
# def meta_user_tags(context, request, va, **kw):
#     brain = kw['brain']
#     api = kw['api']
#     del kw['brain'] #So we don't pass it along as well, causing an argument conflict
#     return api.render_view_group(brain, request, 'user_tags', **kw)

@view_action('metadata_listing', 'reply',
             title = _("Reply"),
             interface = IDiscussionPost,
             ai_perm = ADD_DISCUSSION_POST)
@view_action('metadata_listing', 'counterproposal',
             title = _("Counterproposal"),
             interface = IProposal,
             ai_perm = ADD_PROPOSAL)
def meta_reply(context, request, va, **kw):
    """ Create a reply link.
    """
    if not request.has_permission(va.kwargs['ai_perm'], request.agenda_item):
        return
    query = {'content_type': context.type_name,
             'tag': request.GET.getall('tag'),
             'reply-to': context.uid}
    data = {'role': 'button',
            'class': 'btn btn-default btn-xs',
            'data-reply-to': context.uid,
            'title': '',
            'href': request.resource_url(request.agenda_item, 'add', query = query),
            }
    out = """<a %s><span class="text-primary">%s</span></a> """ % \
        (" ".join(['%s="%s"' % (k, v) for (k, v) in data.items()]),
         request.localizer.translate(va.title))
    return out

@view_action('metadata_listing', 'delete', permission = DELETE, interface = IDiscussionPost)
def meta_delete(context, request, va, **kw):
    if not request.is_moderator:
        return u'<a href="%s" class="btn btn-default btn-xs"><span class="text-danger">%s %s</span></a> ' % \
            (request.resource_url(context, 'delete'),
             '<span class="glyphicon glyphicon-remove"></span>',
             request.localizer.translate(_("Delete")))
