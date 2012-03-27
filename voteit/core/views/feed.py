from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPRedirection
from pyramid.url import resource_url
from pyramid.traversal import find_resource

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IFeedHandler
from voteit.core import fanstaticlib


class FeedView(BaseView):
        
    @view_config(context=IMeeting, name='feed', renderer="templates/meeting_feed.xml", permission=NO_PERMISSION_REQUIRED)
    @view_config(context=IMeeting, name='framefeed', renderer="templates/meeting_framefeed.pt", permission=NO_PERMISSION_REQUIRED)
    def feed(self):
        """ Renders a rss feed for the meeting """
        def _get_url(entry):
            brains = self.api.get_metadata_for_query(uid=entry.context_uid)
            if brains:
                resource = find_resource(self.api.root, brains[0]['path'])
                return resource_url(resource, self.request)
            return resource_url(self.api.meeting(), self.request)

        feed_handler = self.request.registry.getAdapter(self.context, IFeedHandler)
        self.response['entries'] = feed_handler.feed_storage.values()
        self.response['dt_format'] = self.api.dt_util.dt_format
        self.response['active'] = self.context.get_field_value('rss_feed', False);
        self.response['feed_not_active_notice'] = self.api.translate(_(u"This RSS-feed isn't enabled."))
        # only show entries when meeting is ongoing
        self.response['closed'] = self.context.get_workflow_state() == 'closed'
        self.response['get_url'] = _get_url
        return self.response 
