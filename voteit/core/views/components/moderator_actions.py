from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core import VoteITMF as _
from voteit.core.security import DELETE
from voteit.core.security import EDIT
from voteit.core.security import MODERATE_MEETING
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
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
    response = dict(
        context = context,
        menu_content = api.render_view_group(context, request, 'moderator_actions_section', **kw),
    )
    return render('templates/cogwheel/moderator_actions.pt', response, request = request)

@view_action('moderator_actions_section', 'workflow',
             interface = IWorkflowAware, title = _(u"Change workflow state"))
def moderator_actions_wf_section(context, request, va, **kw):
    """ Workflow actions section. """
    api = kw['api']
    response = dict(
        section_title = va.title,
        api = api,
        state_id  = context.get_workflow_state(),
        state_title = context.current_state_title(api.request),
        states = context.get_available_workflow_states(request),
        state_change_url = "%sstate?state=" % api.resource_url(context, request),
    )
    return render('templates/cogwheel/moderator_actions_wf_section.pt', response, request = request)

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
    return render('templates/cogwheel/moderator_actions_section.pt', response, request = request)

@view_action('context_actions', 'edit', title = _(u"Edit"), context_perm = EDIT, viewname = 'edit')
@view_action('context_actions', 'delete', title = _(u"Delete"), context_perm = DELETE, viewname = 'delete')
#@view_action('context_actions', 'move_object', title = _(u"Move"), context_perm = MODERATE_MEETING, viewname = 'move_object')
def moderator_context_action(context, request, va, **kw):
    api = kw['api']
    context_perm = va.kwargs.get('context_perm', None)
    if context_perm and not api.context_has_permission(context_perm, context):
        return ''
    url = "%s%s" % (api.resource_url(context, request), va.kwargs['viewname'])
    return """<li><a href="%s" class="%s">%s</a></li>""" % (url, va.kwargs['viewname'], api.translate(va.title))

@view_action('context_actions', 'poll_config', title = _(u"Poll settings"), interface = IPoll)
def poll_settings_context_action(context, request, va, **kw):
    api = kw['api']
    try:
        schema = context.get_poll_plugin().get_settings_schema()
    except Exception: # pragma: no cover (When plugin has been removed)
        return ''
    if api.context_has_permission(EDIT, context) and schema:
        url = "%spoll_config" % api.resource_url(context, request)
        return """<li><a href="%s">%s</a></li>""" % (url, api.translate(_(u"Poll settings")))
    return ''

@view_action('context_actions', 'enable_proposal_block', title = _(u"Block proposals"),
             interface = IAgendaItem, setting = 'proposal_block', enable = True)
@view_action('context_actions', 'disable_proposal_block', title = _(u"Enable proposals"),
             interface = IAgendaItem, setting = 'proposal_block', enable = False)
@view_action('context_actions', 'enable_discussion_block', title = _(u"Block discussion"),
             interface = IAgendaItem, setting = 'discussion_block', enable = True)
@view_action('context_actions', 'disable_discussion_block', title = _(u"Enable discussion"),
             interface = IAgendaItem, setting = 'discussion_block', enable = False)
def block_specific_perm_action(context, request, va, **kw):
    api = kw['api']
    setting = va.kwargs['setting']
    enabled = context.get_field_value(setting, False)
    if va.kwargs['enable'] == enabled:
        return ''
    url = "%s_toggle_block?%s=" % (request.resource_url(context), setting)
    if enabled:
        url = "%s0" % url
    else:
        url = "%s1" % url
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))

@view_action('context_actions', 'manage_agenda_items',
             interface = IMeeting, permission = EDIT)
def manage_agenda_items(context, request, va, **kw):
    """ Provide a link to the manage agenda items screen.
        Only for moderators and meeting objects.
    """
    api = kw['api']
    #FIXME: Note that order agenda items is a silly name for this view. It should change.
    return """<li><a href="%s">%s</a></li>""" % (request.resource_url(context, 'order_agenda_items'),
                                                 api.translate(_(u"Manage agenda items")))
