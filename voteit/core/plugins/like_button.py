import colander
import deform
from arche.interfaces import IBaseView
from arche.interfaces import IViewInitializedEvent
from arche.security import PERM_VIEW
from arche.views.base import BaseView, DefaultEditForm
from arche_usertags.interfaces import IUserTags
from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.threadlocal import get_current_registry
from repoze.catalog.indexes.keyword import CatalogKeywordIndex

from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.fanstaticlib import like_js
from voteit.core.views.base_edit import ArcheFormCompat
from voteit.core.views.control_panel import control_panel_category
from voteit.core.views.control_panel import control_panel_link
from voteit.core import _
from voteit.core import security


@view_action('metadata_listing', 'like_post',
             permission = PERM_VIEW,
             interface = IDiscussionPost,
             priority = 50)
@view_action('metadata_listing', 'like_prop',
             permission = PERM_VIEW,
             interface = IProposal,
             priority = 50)
def like_action(context, request, va, **kw):
    if context.type_name in request.meeting.like_context_types:
        like = request.registry.getAdapter(context, IUserTags, name = 'like')
        response = {'context': context,
                    'like': like,
                    'user_likes': request.authenticated_userid in like}
        return render('voteit.core.plugins:templates/like_btn.pt', response, request = request)


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
    like_context_types = colander.SchemaNode(
        colander.Set(),
        widget=deform.widget.CheckboxChoiceWidget(values=(
            ('Proposal', _("Proposal")),
            ('DiscussionPost', _("DiscussionPost")),
        ))
    )


def _check_active_for_meeting(context, request, va):
    return bool(context.like_context_types)


def includeme(config):
    from voteit.core.models.meeting import Meeting

    #Set property on meeting
    def get_like_context_types(self):
        return self.get_field_value('like_context_types')
    def set_like_context_types(self, value):
        return self.set_field_value('like_context_types', frozenset(value))
    Meeting.like_context_types = property(get_like_context_types, set_like_context_types)

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
    #Add catalog index
    indexes = {'like_userids': CatalogKeywordIndex(get_like_userids_indexer),}
    config.add_catalog_indexes(__name__, indexes)
    config.add_view(
        LikeSettingsForm,
        context = IMeeting,
        name="like_settings",
        permission=security.MODERATE_MEETING,
        renderer="arche:templates/form.pt",
    )
    #Setup storage
    for iface in (IProposal, IDiscussionPost):
        config.add_usertag('like', iface,
                           catalog_index = 'like_userids',
                           add_perm = PERM_VIEW,
                           view_perm = PERM_VIEW)
        config.add_view(LikeUsersView,
                        context = iface,
                        name = '_like_users_popover',
                        permission = PERM_VIEW,
                        renderer = 'voteit.core.plugins:templates/like_users_popover.pt')
