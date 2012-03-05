from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPRedirection
from pyramid.url import resource_url
from pyramid.traversal import resource_path

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IFeedHandler
from voteit.core import fanstaticlib


class FeedView(BaseView):
        
    @view_config(context=IMeeting, name='feed', renderer="templates/meeting_feed.pt", permission=NO_PERMISSION_REQUIRED)
    def feed(self):
        """ Renders a rss feed for the meeting """
        feed_handler = self.request.registry.getAdapter(self.context, IFeedHandler)
        self.response['entries'] = feed_handler.feed_storage.values()
        self.response['dt_format'] = self.api.dt_util.dt_format
        
        # only show entries when meeting is ongoing
        self.response['closed'] = self.context.get_workflow_state() == 'closed' 
        
        return self.response 
    
    @view_config(context=IMeeting, name='framefeed', renderer="templates/meeting_framefeed.pt", permission=NO_PERMISSION_REQUIRED)
    def feed(self):
        """ Renders a rss feed for the meeting """
        feed_handler = self.request.registry.getAdapter(self.context, IFeedHandler)
        self.response['entries'] = feed_handler.feed_storage.values()
        self.response['dt_format'] = self.api.dt_util.dt_format
        
        # only show entries when meeting is ongoing
        self.response['closed'] = self.context.get_workflow_state() == 'closed' 
        
        return self.response 