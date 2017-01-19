from arche.interfaces import IBaseView
from arche.interfaces import IViewInitializedEvent
from arche.security import PERM_VIEW
from arche.views.base import BaseView
from arche_usertags.interfaces import IUserTags
from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.threadlocal import get_current_registry
from repoze.catalog.indexes.keyword import CatalogKeywordIndex

from voteit.core.models.interfaces import IProposal
from voteit.core.fanstaticlib import support_js
from voteit.core.security import ADD_SUPPORT


@view_action('metadata_listing', 'support_prop',
             permission = PERM_VIEW,
             interface = IProposal,
             priority = 50)
def support_action(context, request, va, **kw):
    support = request.registry.getAdapter(context, IUserTags, name = 'support')
    response = {'context': context,
                'support': support,
                'show_action': request.has_permission(ADD_SUPPORT, context),
                'user_supports': request.authenticated_userid in support}
    return render('voteit.core.plugins:templates/support_btn.pt', response, request = request)

def get_support_userids_indexer(context, default):
    reg = get_current_registry()
    support = reg.queryAdapter(context, IUserTags, name = 'support')
    if support:
        userids = frozenset(support)
        if userids:
            return userids
    return default


class SupportUsersView(BaseView):
    """ This should be a popover, but popover events are broken in
        Twitter bootstrap < 3.3.5 and when this was done i didn't have time to upgrade.
        So right now it's a modal view.
    """
    def __call__(self):
        support = self.request.registry.getAdapter(self.context, IUserTags, name = 'support')
        userids = sorted(support)
        return {'userids': userids}

def support_resources(view, event):
    support_js.need()

def includeme(config):
    config.scan(__name__)
    config.add_subscriber(support_resources, [IBaseView, IViewInitializedEvent])
    #Add catalog index
    indexes = {'support_userids': CatalogKeywordIndex(get_support_userids_indexer),}
    config.add_catalog_indexes(__name__, indexes)
    #Setup storage
    config.add_usertag('support', IProposal,
                       catalog_index = 'support_userids',
                       add_perm = ADD_SUPPORT,
                       view_perm = PERM_VIEW)
    config.add_view(SupportUsersView,
                    context = IProposal,
                    name = '_support_users_popover',
                    permission = PERM_VIEW,
                    renderer = 'voteit.core.plugins:templates/support_users_popover.pt')
