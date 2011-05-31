from pyramid.httpexceptions import HTTPFound

from pyramid.security import remember
from pyramid.security import forget
from pyramid.view import view_config
from pyramid.url import resource_url
from deform import Form
from deform.exception import ValidationFailure

from voteit.core.models.user import get_sha_password
from voteit.core.models.interfaces import IContentUtility
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core import VoteITMF as _
from voteit.core.views.api import APIView


@view_config(context=ISiteRoot, name='login',
             renderer='templates/base_edit.pt')
def login(context, request):
    response = {}
    response['api'] = APIView(context, request)
    content_util = request.registry.getUtility(IContentUtility)
    schema = content_util['User'].schema(context=context, request=request, type='login')
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
        except ValidationFailure, e:
            response['form'] = e.render()
            return response
        
        userid = appstruct['userid']
        password = appstruct['password']

        #userid here can be either an email address or a login name
        if '@' in userid:
            #assume email
            user = context['users'].get_user_by_email(userid)
        else:
            user = context['users'].get(userid)
        
        if IUser.providedBy(user):
            if get_sha_password(password) == user.get_password():
                headers = remember(request, user.__name__)
                return HTTPFound(location = appstruct['came_from'],
                                 headers = headers)
        response['api'].flash_messages.add(_('Login failed.'), type='error')
    
    if 'cancel' in request.POST:
        return HTTPFound(location = referrer)
    
    #Render form
    response['form'] = form.render()
    return response

@view_config(context=ISiteRoot, name='request_password',
             renderer='templates/base_edit.pt')
def request_password(context, request):
    response = {}
    response['api'] = APIView(context, request)
    content_util = request.registry.getUtility(IContentUtility)
    
    schema = content_util['User'].schema(context=context, request=request, type='request_password')
    form = Form(schema, buttons=('request', 'cancel'))
    response['form_resources'] = form.get_widget_resources()

    #Handle submitted information
    if 'request' in request.POST:
        controls = request.POST.items()

        try:
            #appstruct is deforms convention. It will be the submitted data in a dict.
            appstruct = form.validate(controls)
        except ValidationFailure, e:
            response['form'] = e.render()
            return response
        
        userid_or_email = appstruct['userid_or_email']

        #userid here can be either an email address or a login name
        if '@' in userid_or_email:
            #assume email
            user = context['users'].get_user_by_email(userid_or_email)
        else:
            user = context['users'].get(userid_or_email)
        
        if IUser.providedBy(user):
            user.new_request_password_token(request)
            response['api'].flash_messages.add(_('Email sent.'))
            url = resource_url(response['api'].root, request)
            return HTTPFound(location = url)

        response['api'].flash_messages.add(_('Username or email not found.'), type='error')
    
    if 'cancel' in request.POST:
        url = resource_url(response['api'].root, request)
        return HTTPFound(location = url)

    #Render form
    response['form'] = form.render()
    return response
    
    
@view_config(context=ISiteRoot, name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location = resource_url(request.context, request),
                     headers = headers)