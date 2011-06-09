import re

from pyramid.security import authenticated_userid
from pyramid.exceptions import Forbidden
from pyramid.view import view_config
from pyramid.url import resource_url
from webob.exc import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.traversal import find_interface

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.message import Messages


class MessagesView(object):

    def __init__(self, request):
        self.request = request
        self.context = request.context
        self.messages = Messages(request)

        self.response = {}

    @view_config(name="_set_message", context=IBaseContent)
    def set_message(self):
        """ View for setting or removing expression tags like 'Like' or 'Support'.
            the request.POST object must contain tag and do.
            This view is usually loaded inline, but it's possible to call without js.
        """
        request = self.request
        context = self.context
        
        #FIXME: Use normal colander Schema + CSRF?
        userid = authenticated_userid(request)
        if not userid:
            raise Forbidden("You're not allowed to access this view.")
            
        meeting = find_interface(context, IMeeting)
        
        self.messages.add(meeting.uid, 'test', 'log')
    
        return Response(self.get_messages())

    def get_messages(self, userid=None):
        meeting = find_interface(self.request.context, IMeeting)
        
        if meeting and meeting.uid:
            messages = self.messages.retrieve_messages(meeting.uid, userid=userid, )
        else:
            messages = None

        self.response['messages'] = messages

        return render('templates/macros/messages.pt', self.response, request=self.request)
