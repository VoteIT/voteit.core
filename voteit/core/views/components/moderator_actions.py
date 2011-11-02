from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import find_resource

from voteit.core import VoteITMF as _
from voteit.core.security import DELETE
from voteit.core.security import EDIT
from voteit.core.security import MODERATE_MEETING
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IWorkflowAware


@view_action('main', 'moderator_actions', title=_(u"Moderator actions"), permission = MODERATE_MEETING)
def moderator_actions(context, request, va, **kw):
    """ A.k.a. the cogwheel menu. This view action will render the
        required HTML, while anything in the view group 'moderator_actions'
        will be contained as menu sections. The sections in turn will contain
        menu alternatives.
    """
    api = kw['api']
    if not IBaseContent.providedBy(context):
        #Assume brain - might need to change this later
        context = find_resource(api.root, context['path'])
    response = dict(
        menu_content = api.render_view_group(context, request, 'moderator_actions_section', **kw),
    )
    return render('../templates/snippets/moderator_actions.pt', response, request = request)

@view_action('moderator_actions_section', 'workflow',
             interface = IWorkflowAware, title = _(u"Change workflow state"))
def moderator_actions_wf_section(context, request, va, **kw):
    """ Workflow actions section. """
    api = kw['api']
    response = dict(
        section_title = va.title,
        api = api,
        state_id  = context.get_workflow_state(),
        states = context.get_available_workflow_states(request),
        state_change_url = "%s@@state?state=" % api.resource_url(context, request),
    )
    return render('../templates/snippets/moderator_actions_wf_section.pt', response, request = request)

@view_action('moderator_actions_section', 'context_actions',
             title = _(u"Actions here"), contained_section = 'context_actions')
def moderator_actions_section(context, request, va, **kw):
    """ Generic moderator actions section. """
    api = kw['api']
    response = dict(
        section_title = va.title,
        api = api,
        section_data = api.render_view_group(context, request, va.kwargs['contained_section'], **kw),
    )
    return render('../templates/snippets/moderator_actions_section.pt', response, request = request)

@view_action('context_actions', 'edit', title = _(u"Edit"), context_perm = EDIT, viewname = '@@edit')
@view_action('context_actions', 'delete', title = _(u"Delete"), context_perm = DELETE, viewname = '@@delete')
def moderator_context_action(context, request, va, **kw):
    api = kw['api']
    context_perm = va.kwargs.get('context_perm', None)
    if context_perm and not api.context_has_permission(context_perm, context):
        return ''
    url = "%s%s" % (api.resource_url(context, request), va.kwargs['viewname'])
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))

@view_action('context_actions', 'poll_config', title = _(u"Poll settings"), interface = IPoll)
def poll_settings_context_action(context, request, va, **kw):
    api = kw['api']
    schema = context.get_poll_plugin().get_settings_schema()
    if api.context_has_permission(EDIT, context) and schema:
        url = "%s@@poll_config" % api.resource_url(context, request)
        return """<li><a href="%s">%s</a></li>""" % (url, api.translate(_(u"Poll settings")))
    return ''
