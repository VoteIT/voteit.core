from pyramid.httpexceptions import HTTPFound

from pyramid.security import remember
from pyramid.security import forget
from pyramid.view import view_config
from pyramid.url import resource_url
from deform import Form

from voteit.core.models.user import get_sha_password, LoginSchema
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core import VoteITMF as _
from voteit.core.views.api import APIView


@view_config(context=ISiteRoot, name='login',
             renderer='templates/base_edit.pt')
def login(context, request):
    response = {}
    response['api'] = APIView(context, request)
    schema = LoginSchema()
    form = Form(schema, buttons=('login', 'cancel'))
    response['form_resources'] = form.get_widget_resources()

    #Came from
    referrer = request.url
    if referrer.endswith('login'):
        referrer = '/' # never use the login form itself as came_from
    schema['came_from'].default = referrer

    #Handle submitted information
    if 'login' in request.POST:
        controls = request.POST.items()

        try:
            #appstruct is deforms convention. It will be the submitted data in a dict.
            appstruct = form.validate(controls)
            #FIXME: validate name - it must be unique and url-id-like
        except ValidationFailure, e:
            response['form'] = e.render()
            response['message'] = _('Login failed.')
            return response
        
        userid = appstruct['userid']
        password = appstruct['password']

        user = context['users'].get(userid)
        if IUser.providedBy(user):
            if get_sha_password(password) == user.get_password():
                headers = remember(request, userid)
                return HTTPFound(location = appstruct['came_from'],
                                 headers = headers)
        message = _('Login failed.')
    
    #Render form
    response['form'] = form.render()
    return response

    
@view_config(context=ISiteRoot, name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location = resource_url(request.context, request),
                     headers = headers)