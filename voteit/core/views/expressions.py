import re
from pyramid.security import authenticated_userid
from pyramid.exceptions import Forbidden
from pyramid.view import view_config
from pyramid.url import resource_url
from webob.exc import HTTPFound

from pyramid.response import Response

from voteit.core.models.interfaces import IBaseContent
from voteit.core.models.expression_adapter import Expressions

from voteit.core.views.api import APIView

TAG_PATTERN = re.compile(r'^[a-zA-Z]{1,10}$')

        
@view_config(name="set_expression", context=IBaseContent)
def expression_action(context, request):
    """ View for setting or removing expression tags like 'Like' or 'Support'.
        the request.POST object must contain tag and do.
    """
    userid = authenticated_userid(request)
    if not userid:
        raise Forbidden("You're not allowed to access this view.")
    
    tag = request.POST.get('tag')
    if tag is None:
        raise ValueError("'tag' isn't set.")
    if not TAG_PATTERN.match(tag):
        raise ValueError("'tag' doesn't conform to tag standard: '^[a-zA-Z]{1,10}$'")
    
    do = int(request.POST.get('do')) #0 for remove, 1 for add
    
    expressions = Expressions(request)
    
    if do:
        expressions.add(tag, userid, context.uid)

    if not do:
        expressions.remove(tag, userid, context.uid)
        
    display_name = request.POST.get('display_name')
    if display_name == '':
        display_name = None

    if not request.is_xhr:
        #FIXME: This should probably not happen later on. But it's usefull for testing
        return HTTPFound(location=resource_url(context, request))
    else:
        #FIXME: This must be done a bit more elegant, display_name should be past as well 
        api = APIView(context, request)
        return Response(api.get_user_expressions(context, tag, userid, display_name))
