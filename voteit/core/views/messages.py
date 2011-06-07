import re
from pyramid.security import authenticated_userid
from pyramid.exceptions import Forbidden
from pyramid.view import view_config
from pyramid.url import resource_url
from webob.exc import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.message import Messages


class MessagesView(object):

    def __init__(self, request):
        self.request = request
        self.messages = Messages(request)

#    @view_config(name="_set_expression", context=IBaseContent)
#    def set_expression(self):
#        """ View for setting or removing expression tags like 'Like' or 'Support'.
#            the request.POST object must contain tag and do.
#            This view is usually loaded inline, but it's possible to call without js.
#        """
#        context = self.request.context
#        request = self.request
#        
#        #FIXME: Use normal colander Schema + CSRF?
#        userid = authenticated_userid(request)
#        if not userid:
#            raise Forbidden("You're not allowed to access this view.")
#        
#        tag = request.POST.get('tag')
#        if tag is None:
#            raise ValueError("'tag' isn't set.")
#        if not TAG_PATTERN.match(tag):
#            raise ValueError("'tag' doesn't conform to tag standard: '^[a-zA-Z]{1,10}$'")
#        
#        do = int(request.POST.get('do')) #0 for remove, 1 for add
#                
#        if do:
#            self.expressions.add(tag, userid, context.uid)
#    
#        if not do:
#            self.expressions.remove(tag, userid, context.uid)
#            
#        display_name = request.POST.get('display_name')
#        if display_name == '':
#            display_name = None
#    
#        if not request.is_xhr:
#            return HTTPFound(location=resource_url(context, request))
#        else:
#            return Response(self.get_expressions(context, tag, userid, display_name))

    def get_messages(self, userid, meeting_uid):
        userid = authenticated_userid(self.request)

        messages = self.messages.retrieve_user_messages(userid)

        response = {}
        response['messages'] = messages

        return render('templates/macros/messages.pt', response, request=self.request)
        
