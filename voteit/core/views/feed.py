import pytz

from pyramid.renderers import render
from pyramid.response import Response
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.traversal import find_resource
from pyramid.view import view_config
from pyramid.url import resource_url

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IFeedHandler
from voteit.core import fanstaticlib


class FeedView(BaseView):
    
    @view_config(context=IMeeting, name='feed', permission=NO_PERMISSION_REQUIRED)
    def feed(self):
        """ Renders a rss feed for the meeting """
        
        return Response(render("templates/meeting_feed.xml", self._get_feed(), request = self.request), content_type='application/rss+xml') 
    
    @view_config(context=IMeeting, name='framefeed', renderer="templates/meeting_framefeed.pt", permission=NO_PERMISSION_REQUIRED)
    def framefeed(self):
        """ Renders a html feed for the meeting """
        
        return self._get_feed()
          
    def _get_feed(self):
        ''' Makes a respone dict for renderers '''
        def _get_url(entry):
            brains = self.api.get_metadata_for_query(uid=entry.context_uid)
            if brains:
                resource = find_resource(self.api.root, brains[0]['path'])
                return resource_url(resource, self.request)
            return resource_url(self.api.meeting, self.request)
        
        # Borrowed from PyRSS2Gen, thanks for this workaround
        def _format_date(dt):
            # added to convert the datetime to GTM timezone
            tz = pytz.timezone('GMT')
            dt = tz.normalize(dt.astimezone(tz))
            
            """convert a datetime into an RFC 822 formatted date
        
            Input date must be in GMT.
            """
            # Looks like:
            #   Sat, 07 Sep 2002 00:00:01 GMT
            # Can't use strftime because that's locale dependent
            #
            # Isn't there a standard way to do this for Python?  The
            # rfc822 and email.Utils modules assume a timestamp.  The
            # following is based on the rfc822 module.
            return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (
                    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()],
                    dt.day,
                    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][dt.month-1],
                    dt.year, dt.hour, dt.minute, dt.second)

        feed_handler = self.request.registry.getAdapter(self.context, IFeedHandler)
        self.response['entries'] = feed_handler.feed_storage.values()
        self.response['format_date'] = _format_date
        self.response['active'] = self.context.get_field_value('rss_feed', False);
        self.response['feed_not_active_notice'] = self.api.translate(_(u"This RSS-feed isn't enabled."))
        # only show entries when meeting is ongoing
        self.response['closed'] = self.context.get_workflow_state() == 'closed'
        self.response['get_url'] = _get_url
        return self.response