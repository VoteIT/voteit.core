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
from voteit.core.models.expression import Expressions


TAG_PATTERN = re.compile(r'^[a-zA-Z]{1,10}$')



class ExpressionsView(object):

    def __init__(self, request):
        self.request = request
        self.expressions = Expressions(request)

    @view_config(name="_set_expression", context=IBaseContent)
    def set_expression(self):
        """ View for setting or removing expression tags like 'Like' or 'Support'.
            the request.POST object must contain tag and do.
            This view is usually loaded inline, but it's possible to call without js.
        """
        context = self.request.context
        request = self.request
        
        #FIXME: Use normal colander Schema + CSRF?
        userid = authenticated_userid(request)
        if not userid:
            raise Forbidden("You're not allowed to access this view.")
        
        tag = request.POST.get('tag')
        if tag is None:
            raise ValueError("'tag' isn't set.")
        if not TAG_PATTERN.match(tag):
            raise ValueError("'tag' doesn't conform to tag standard: '^[a-zA-Z]{1,10}$'")
        
        do = int(request.POST.get('do')) #0 for remove, 1 for add
                
        if do:
            self.expressions.add(tag, userid, context.uid)
    
        if not do:
            self.expressions.remove(tag, userid, context.uid)
            
        display_name = request.POST.get('display_name')
        if display_name == '':
            display_name = None
    
        if not request.is_xhr:
            return HTTPFound(location=resource_url(context, request))
        else:
            return Response(self.get_expressions(context, tag, userid, display_name))

    def get_expressions(self, context, tag, userid, display_name):
        userids = list(self.expressions.retrieve_userids(tag, context.uid))

        response = {}
        response['context_id'] = context.uid
        response['toggle_url'] = "%s_set_expression" % resource_url(context, self.request)
        response['tag'] = tag
        response['display_name'] = display_name
        
        if userid and userid in userids:
            response['button_txt'] = "%s %s" % (_(u"Remove"), display_name)
            response['selected'] = True
            response['do'] = "0"
            userids.remove(userid)
        else:
            response['button_txt'] = "%s" % display_name
            response['selected'] = False
            response['do'] = "1"
        
        response['over_limit'] = 0
        limit = 5
        if len(userids) > limit:
            response['over_limit'] = len(userids) - limit            
        response['userids'] = userids[:limit]
        
        return render('templates/macros/expressions.pt', response, request=self.request)
        
