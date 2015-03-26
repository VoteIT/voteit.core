from __future__ import unicode_literals
from uuid import uuid4

from arche.views.base import BaseView
from pyramid.view import view_config
from pyramid.traversal import resource_path

from voteit.core.models.interfaces import IMeeting
from voteit.core import security


@view_config(context = IMeeting, name = 'watcher_data.json', renderer = 'json', permission = security.VIEW)
class WatcherView(BaseView):

    def __call__(self):
        #FIXME: Caching
        #print 'cachekey:', self.request.GET.get('cachekey', '')
        response = {}
        #Ongoing polls
        query = "type_name == 'Poll' and workflow_state == 'ongoing' and path == '%s'" % resource_path(self.context)
        unvoted_polls = []
        for obj in self.catalog_query(query, resolve = True):
            if self.request.has_permission(security.ADD_VOTE, obj) and self.request.authenticated_userid not in obj:
                unvoted_polls.append(obj)
        response['unvoted_polls'] = len(unvoted_polls)
        return response
