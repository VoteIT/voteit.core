from arche.interfaces import IBaseView
from arche.interfaces import IViewInitializedEvent
from arche.security import PERM_VIEW
from arche.views.base import BaseView
from arche_usertags.interfaces import IUserTags
from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.threadlocal import get_current_registry
from repoze.catalog.indexes.keyword import CatalogKeywordIndex

from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IProposal
from voteit.core.fanstaticlib import like_js


@view_action('metadata_listing', 'like_post',
             permission = PERM_VIEW,
             interface = IDiscussionPost,
             priority = 50)
@view_action('metadata_listing', 'like_prop',
             permission = PERM_VIEW,
             interface = IProposal,
             priority = 50)
def like_action(context, request, va, **kw):
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

def includeme(config):
    config.scan(__name__)
    config.add_subscriber(like_resources, [IBaseView, IViewInitializedEvent])
    #Add catalog index
    indexes = {'like_userids': CatalogKeywordIndex(get_like_userids_indexer),}
    config.add_catalog_indexes(__name__, indexes)
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
