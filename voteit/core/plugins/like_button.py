from __future__ import unicode_literals

import colander
from arche.interfaces import IBaseView
from arche.interfaces import IViewInitializedEvent
from arche.security import PERM_VIEW
from arche.views.base import BaseView, DefaultEditForm
from arche_usertags.interfaces import IUserTags
from betahaus.viewcomponent import view_action
from deform import widget
from pyramid.renderers import render
from pyramid.threadlocal import get_current_registry
from pyramid.traversal import find_interface
from repoze.catalog.indexes.keyword import CatalogKeywordIndex

from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.fanstaticlib import like_js
from voteit.core.schemas.proposal import proposal_states_widget
from voteit.core.views.base_edit import ArcheFormCompat
from voteit.core.views.control_panel import control_panel_category
from voteit.core.views.control_panel import control_panel_link
from voteit.core import _
from voteit.core import security


LIKE_SETTING_ACTIVE = 0
LIKE_SETTING_INACTIVE = 1
LIKE_SETTING_HIDDEN = 2
LIKE_SETTING_VALUES = (
    (0, _('Active')),
    (1, _('Inactive')),
    (2, _('Hidden')),
)


def _check_add_perm(adapter, request):
    if request.meeting is None:
        meeting = find_interface(adapter.context, IMeeting)
    else:
        meeting = request.meeting
    like_context_types = meeting.like_context_types
    like_workflow_states = meeting.like_workflow_states
    like_user_roles = meeting.like_user_roles
    user_meeting_roles = meeting.local_roles.get(request.authenticated_userid, ())

    # Check if context can be liked
    if not like_context_types or adapter.context.type_name not in like_context_types:
        return False

    # If proposal, check if workflow state can be liked
    if IProposal.providedBy(adapter.context):
        if like_workflow_states and adapter.context.get_workflow_state() not in like_workflow_states:
            return False

    # Lastly, check if user has a role that can like
    if like_user_roles and not like_user_roles.intersection(user_meeting_roles):
        return False

    return True


@view_action('metadata_listing', 'like_post',
             permission = PERM_VIEW,
             interface = IDiscussionPost,
             priority = 50)
@view_action('metadata_listing', 'like_prop',
             permission = PERM_VIEW,
             interface = IProposal,
             priority = 50)
def like_action(context, request, va, **kw):
    context_types = request.meeting.like_context_types
    workflow_states = request.meeting.like_workflow_states
    state = request.meeting.like_button_state
    success_threshold = request.meeting.like_success_threshold

    if state == LIKE_SETTING_HIDDEN:
        return
    if not context_types or context.type_name not in context_types:
        return
    if IProposal.providedBy(context):
        if workflow_states and context.get_workflow_state() not in workflow_states:
            return
    like = request.registry.getAdapter(context, IUserTags, name = 'like')
    try:
        has_like_perm = request._has_like_perm
    except AttributeError:
        request._has_like_perm = has_like_perm = _check_add_perm(like, request)
    response = {'context': context,
                'like': like,
                'has_like_perm': has_like_perm,
                'user_likes': request.authenticated_userid in like,
                'success': (success_threshold > 0) and (len(like) >= success_threshold)}
    if state == LIKE_SETTING_ACTIVE:
        template_name = 'voteit.core.plugins:templates/like_btn.pt'
    else:
        template_name = 'voteit.core.plugins:templates/like_btn_readonly.pt'
    return render(template_name, response, request=request)


def get_like_userids_indexer(context, default):
    reg = get_current_registry()
    like = reg.queryAdapter(context, IUserTags, name = 'like')
    if like:
        userids = frozenset(like)
        if userids:
            return userids
    return default


class LikeUsersView(BaseView):
    """ This should be a popover, but popover events are broken in
        Twitter bootstrap < 3.3.5 and when this was done i didn't have time to upgrade.
        So right now it's a modal view.
    """

    def __call__(self):
        like = self.request.registry.getAdapter(self.context, IUserTags, name = 'like')
        userids = sorted(like)
        return {'userids': userids}


def like_resources(view, event):
    like_js.need()


class LikeSettingsForm(ArcheFormCompat, DefaultEditForm):
    type_name = 'Meeting'
    schema_name = 'like_settings'
    title = _("Like button")


class LikeSettingsSchema(colander.Schema):
    like_button_state = colander.SchemaNode(
        colander.Int(),
        widget=widget.RadioChoiceWidget(values=LIKE_SETTING_VALUES, inline=True),
        title=_('Like button state'),
        default=LIKE_SETTING_ACTIVE,
    )
    like_success_threshold = colander.SchemaNode(
        colander.Int(),
        title=_('Success threshold'),
        description=_('Show like button in success color from this amount of likes. Set to "0" to disable.'),
        default=0,
    )
    like_context_types = colander.SchemaNode(
        colander.Set(),
        widget=widget.CheckboxChoiceWidget(values=(
            ('Proposal', _("Proposal")),
            ('DiscussionPost', _("DiscussionPost")),
        ), inline=True),
        title=_("Allow like on these types"),
    )
    like_workflow_states = colander.SchemaNode(
        colander.Set(),
        title=_('Proposal workflow states'),
        description=_('If selected, proposals in these workflow states can be liked.'),
        widget=proposal_states_widget,
        missing=(),
    )
    like_user_roles = colander.SchemaNode(
        colander.Set(),
        title=_('User roles'),
        description=_("like_user_roles_description",
                      default='If selected, users will need one of these within '
                      'the meeting to be able to like something.'),
        widget=widget.CheckboxChoiceWidget(values=security.MEETING_ROLES),
        missing=(),
    )


def _check_active_for_meeting(context, request, va):
    return bool(context.like_context_types)


def includeme(config):
    from voteit.core.models.meeting import Meeting

    # Set properties on meeting
    Meeting.add_field('like_context_types', wrapper=frozenset)
    Meeting.add_field('like_workflow_states', wrapper=frozenset)
    Meeting.add_field('like_user_roles', wrapper=frozenset)
    Meeting.add_field('like_button_state', default=LIKE_SETTING_ACTIVE)
    Meeting.add_field('like_success_threshold', default=0)

    config.add_schema('Meeting', LikeSettingsSchema, 'like_settings')
    config.add_view_action(control_panel_category,
                           'control_panel', 'like',
                           panel_group='control_panel_like',
                           title=_("Like button"),
                           check_active=_check_active_for_meeting)
    config.add_view_action(control_panel_link,
                           'control_panel_like', 'settings',
                           title=_("Settings"), view_name='like_settings')
    config.scan(__name__)
    config.add_subscriber(like_resources, [IBaseView, IViewInitializedEvent])
    # Add catalog index
    indexes = {'like_userids': CatalogKeywordIndex(get_like_userids_indexer),}
    config.add_catalog_indexes(__name__, indexes)
    config.add_view(
        LikeSettingsForm,
        context = IMeeting,
        name="like_settings",
        permission=security.MODERATE_MEETING,
        renderer="arche:templates/form.pt",
    )
    # Setup storage
    for iface in (IProposal, IDiscussionPost):
        config.add_usertag('like', iface,
                           catalog_index = 'like_userids',
                           add_perm = PERM_VIEW,
                           view_perm = PERM_VIEW,
                           add_perm_callback = _check_add_perm)
        config.add_view(LikeUsersView,
                        context = iface,
                        name = '_like_users_popover',
                        permission = PERM_VIEW,
                        renderer = 'voteit.core.plugins:templates/like_users_popover.pt')
