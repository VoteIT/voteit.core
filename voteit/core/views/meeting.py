from pyramid.security import has_permission
from pyramid.view import view_config
from webob.exc import HTTPFound
import deform

from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core import security
from pyramid.exceptions import Forbidden


class MeetingView(BaseView):
    
    @view_config(context=IMeeting, renderer="templates/base_view.pt")
    def meeting_view(self):
        """ Meeting view behaves a bit differently than regular views since
            it should allow users to request access if unauthorized is raised.
        """
        if not has_permission(security.VIEW, self.context, self.request):
            
            #If user is authenticated:
            if has_permission(security.REQUEST_MEETING_ACCESS, self.context, self.request):
                url = self.api.resource_url(self.context, self.request) + 'request_meeting_access'
                return HTTPFound(location = url)
            
            #Otherwise raise unauthorized
            raise Forbidden("You can't request access to this meeting. Maybe you need to login, or it isn't allowed.")
        
        return self.response

    @view_config(name="request_meeting_access", context=IMeeting,
                 permission=security.REQUEST_MEETING_ACCESS,
                 renderer="templates/base_edit.pt")
    def request_meeting_access_view(self):
        """ View for users who don't have access to a meeting to request it. """
        
        schema = self.api.content_info['Meeting'].schema(type='request_access')
        self.form = deform.Form(schema, buttons=('submit', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'submit' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = self.form.validate(controls)
                #FIXME: validate name - it must be unique and url-id-like
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            self.request.sqldb.execute('insert into pending_meeting_access_requests (meeting_uid, userid, message) values (?, ?, ?)',
                                       [self.context.uid, self.api.userid, appstruct['message']])
            self.request.sqldb.commit()
            
            #Redirect to root
            url = self.api.resource_url(self.api.root, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = self.api.resource_url(self.api.root, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response

    @view_config(name="pending_access_requests", context=IMeeting,
                 permission=security.MODERATE_MEETING,
                 renderer="templates/pending_access_requests.pt")
    def pending_access_requests_view(self):
        
        result = self.request.sqldb.execute("select id, userid, message from pending_meeting_access_requests where meeting_uid = '%s'" % self.context.uid)
        access_requests = []
        for row in result.fetchall():
            item = {}
            item['id'] = row[0]
            item['userid'] = row[1]
            item['message'] = row[2]
            access_requests.append(item)
        
        self.response['access_requests'] = access_requests

        return self.response
    