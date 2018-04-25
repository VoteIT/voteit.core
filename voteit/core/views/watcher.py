from __future__ import unicode_literals

from arche.views.base import BaseView
from betahaus.viewcomponent.decorators import view_action
from pyramid.traversal import resource_path
from pyramid.view import view_config
from repoze.catalog.query import Any
from repoze.catalog.query import Eq

from voteit.core.models.interfaces import IMeeting
from voteit.core import security


@view_config(context = IMeeting, name = 'watcher_data.json', renderer = 'json', permission = security.VIEW)
class WatcherView(BaseView):
    """ Fetch everything in the view group watcher_json and return it as a json response.
        Each view groups name will be the same as the json key.
        So the view action below with name 'unvoted_polls' will have the key 'unvoted_polls'.
        This way other plugins may inject results here and then add callbacks to the watcher javascript.
        See js/watcher.js
    """

    def __call__(self):
        #FIXME: Caching
        #print 'cachekey:', self.request.GET.get('cachekey', '')
        if self.request.authenticated_userid:
            return self.render_view_group('watcher_json', as_type = 'dict', empty_val = '',
                                          meeting_path = resource_path(self.context))
        return {}


_unvoted_query = Eq('type_name', 'Poll') & Eq('workflow_state', 'ongoing')


@view_action('watcher_json', 'unvoted_polls')
def unvoted_polls(context, request, va, **kw):
    """ Return a count for """
    if security.ROLE_VOTER not in context.local_roles.get(request.authenticated_userid, ()):
        return
    view = kw['view']
    query = _unvoted_query & Eq('path', kw['meeting_path'])
    counter = 0
    for obj in view.catalog_query(query, resolve = True):
        if request.authenticated_userid not in obj and request.has_permission(security.ADD_VOTE, obj):
            counter+=1
    return counter


@view_action('watcher_json', 'agenda_states')
def agenda_states(context, request, va, **kw):
    states = ['ongoing', 'upcoming', 'closed']
    if request.is_moderator:
        states.append('private')
    tag = request.session.get('voteit.ai_selected_tag', '')
    if tag in context.tags:
        tag = tag.lower()
    else:
        tag = None
    results = {}
    query = Eq('path', kw['meeting_path']) & Eq('type_name', 'AgendaItem')
    for state in states:
        squery = query & Eq('workflow_state', state)
        res = request.root.catalog.query(squery)[0]
        if res.total:
            if tag:
                tagres = request.root.catalog.query(squery & Any('tags', [tag]))[0]
                results[state] = "%s / %s" % (tagres.total, res.total)
            else:
                results[state] = str(res.total)
        else:
            results[state] = ""
    return results
