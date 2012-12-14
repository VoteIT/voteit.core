from pyramid.renderers import render
from betahaus.viewcomponent import view_action

from voteit.core import VoteITMF as _


@view_action('main', 'global_actions')
def global_actions(context, request, va, **kw):
    """ The main global actions view component which will render the rest of them. """
    api = kw['api']
    response = {}
    response['api'] = api
    if not api.userid:
        return u""
    return render('templates/header/global_actions.pt', response, request = request)

@view_action('global_actions_authenticated', 'logout')
def logout_action(context, request, va, **kw):
    api = kw['api']
    link = request.application_url + '/logout'
    return u"""<li><a href="%s" class="logout icon"><span>%s</span></a></li>""" % (link, api.translate(_(u"Logout")))
