import re

from pyramid.security import authenticated_userid
from pyramid.exceptions import Forbidden
from pyramid.view import view_config
from pyramid.url import resource_url
from webob.exc import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.i18n import get_localizer

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.interfaces import ISQLSession
from voteit.core.models.expression import Expressions


TAG_PATTERN = re.compile(r'^[a-zA-Z]{1,10}$')


class ExpressionsView(object):

    def __init__(self, request):
        self.request = request
        self.sql_session = request.registry.getUtility(ISQLSession)()
        self.expressions = Expressions(self.sql_session)
        self.localizer = get_localizer(request)

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
        expl_display_name = request.POST.get('expl_display_name')
    
        if not request.is_xhr:
            return HTTPFound(location=resource_url(context, request))
        else:
            return Response(self.get_expressions(context, tag, userid, display_name, expl_display_name))

    def get_expressions(self, context, tag, userid, display_name, expl_display_name):
        userids = list(self.expressions.retrieve_userids(tag, context.uid))

        response = {}
        response['context_id'] = context.uid
        response['toggle_url'] = "%s_set_expression" % resource_url(context, self.request)
        response['tag'] = tag
        response['display_name'] = display_name
        
        if userid and userid in userids:
            #Note: It's not possible to have nested translation strings. Hence this
            response['button_label'] = _(u"Remove ${display_name}",
                                         mapping={'display_name':self.localizer.translate(display_name)})
            response['selected'] = True
            response['do'] = "0"
            userids.remove(userid)
        else:
            response['button_label'] = display_name
            response['selected'] = False
            response['do'] = "1"
        
        response['has_entries'] = bool(response['selected'] or userids)
        response['userids'] = userids
        #This label is for after the listing, could be "4 people like this"
        response['expl_display_name'] = expl_display_name
        
        return render('templates/macros/expressions.pt', response, request=self.request)
        
