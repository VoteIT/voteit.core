from pyramid.renderers import render
from betahaus.viewcomponent import view_action

from voteit.core import VoteITMF as _


@view_action('main', 'global_actions')
def global_actions(context, request, va, **kw):
    """ The main global actions view component which will render the rest of them. """
    api = kw['api']
    response = {}
    response['api'] = api
    response['meeting_time'] = api.dt_util.dt_format(api.dt_util.utcnow())
    return render('../templates/snippets/global_actions.pt', response, request = request)


@view_action('global_actions_anon', 'login')
def action_login(context, request, va, **kw):
    api = kw['api']
    link = request.application_url + '/login'
    return """<li><a href="%s">%s</a></li>""" % (link, api.translate(_(u"Login")))


@view_action('global_actions_anon', 'register')
def action_register(context, request, va, **kw):
    api = kw['api']
    link = request.application_url + '/register'
    return """<li><a href="%s">%s</a></li>""" % (link, api.translate(_(u"Register")))


@view_action('global_actions_authenticated', 'user_profile')
def user_profile_action(context, request, va, **kw):
    api = kw['api']
    profile_url = api.resource_url(api.user_profile, request)
    return u"""<li><a href="%s" class="user icon"><span>%s</span></a></li>""" % (profile_url, api.user_profile.title)


@view_action('global_actions_authenticated', 'logout')
def logout_action(context, request, va, **kw):
    api = kw['api']
    link = request.application_url + '/logout'
    return u"""<li><a href="%s" class="logout icon"><span>%s</span></a></li>""" % (link, api.translate(_(u"Logout")))
