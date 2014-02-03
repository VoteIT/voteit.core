from socket import error as SMTPError #At least in this case :)

from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPServerError
from pyramid.security import NO_PERMISSION_REQUIRED

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.views.api import APIView


class ExceptionView(object):
    """ Exception view, for error messages.
        Note that context might not be related to what caused the error.
    """

    def __init__(self, exception, request):
        self.exception = exception
        self.context = request.context
        self.request = request
        self.api = APIView(request.context, request)
    
    @view_config(context=HTTPForbidden, permission=NO_PERMISSION_REQUIRED, xhr=False)
    def forbidden_view(self):
        """ I.e. 403. If it is a xhr request return Forbidden else 
            find first context where user has view permission
            if they're logged in, otherwise redirect to login form.
        """
        self.api.flash_messages.add(self.exception.detail,
                                    type = 'error',
                                    close_button = False)
        # is user logged in
        if self.api.userid:
            obj = self.context
            while obj.__parent__:
                if self.api.context_has_permission(security.VIEW, obj):
                    url = resource_url(obj, self.request)
                    return HTTPFound(location = url)
                obj = obj.__parent__
            return HTTPFound(location = self.request.application_url)
        #Redirect to login
        return HTTPFound(location="%s/login?came_from=%s" %(self.request.application_url, self.request.url))

    @view_config(context = HTTPNotFound, permission = NO_PERMISSION_REQUIRED, xhr = False)
    def not_found_view(self):
        """ I.e. 404. If it is a xhr request return NotFound else
            find first context where user has view permission 
        """
        err_msg = _(u"404_error_msg",
                    default = u"Can't find anything at '${path}'. Maybe it has been removed?",
                    mapping = {'path': self.exception.detail})
        
        if self.request.is_xhr:
            return HTTPNotFound(err_msg)
        self.api.flash_messages.add(err_msg,
                                    type = 'error',
                                    close_button = False)
        return HTTPFound(location = _find_good_redirect_url(self.context, self.request, self.api))

    @view_config(context = SMTPError, permission = NO_PERMISSION_REQUIRED)
    def smtp_error_view(self):
        """ SMTP connection error caused during transaction commits.
            Note that the SMTP action is performed after the request has completed.
            In other words, things may be committed to database even though send failed.
        """
        err_msg = _(u"smtp_error_msg",
                    default = u"There was an error while sending mail. "
                        u"Error was: ${exc_txt}",
                    mapping = {'exc_txt': unicode(self.exception)})
        self.api.flash_messages.add(err_msg,
                                    type = 'error')
        return HTTPFound(location = _find_good_redirect_url(self.context, self.request, self.api))


def _find_good_redirect_url(context, request, api):
    if hasattr(context, '__parent__'):
        while context.__parent__:
            if api.context_has_permission(security.VIEW, context):
                return request.resource_url(context)
            context = context.__parent__
    return request.application_url
