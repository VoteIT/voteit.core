from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core.models.interfaces import IUser


@view_action('email', 'request_password', interface = IUser)
def request_password_body(context, request, va, **kw):
    """ Body for request password email """
    response = dict(
        pw_link = kw['pw_link'],
        context = context,
    )
    return render('../templates/email/request_password.pt', response, request = request)
