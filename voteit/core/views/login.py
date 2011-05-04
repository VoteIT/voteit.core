from pyramid.httpexceptions import HTTPFound

from pyramid.security import remember
from pyramid.security import forget
from pyramid.view import view_config
from pyramid.url import resource_url

from voteit.core.models.user import get_sha_password
from voteit.core.models.interfaces import IUser
from voteit.core import VoteITMF as _
from voteit.core.models.site import SiteRoot
from voteit.core.views.api import APIView


@view_config(context=SiteRoot, name='login',
             renderer='templates/login.pt')
def login(context, request):
    login_url = resource_url(request.context, request, 'login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    userid = ''
    password = ''

    if 'form.submitted' in request.params:
        userid = request.params['userid']
        password = request.params['password']
        
        user = context.users.get(userid)
        if IUser.providedBy(user):
            if get_sha_password(password) == user.get_password():
                headers = remember(request, login)
                return HTTPFound(location = came_from,
                                 headers = headers)
        message = _('Login failed.')

    return dict(
        message = message,
        url = request.application_url + '/login',
        came_from = came_from,
        userid = userid,
        password = password,
        api = APIView(context, request),
        )
    
@view_config(context=SiteRoot, name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location = resource_url(request.context, request),
                     headers = headers)