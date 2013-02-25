from betahaus.viewcomponent import view_action

from voteit.core import VoteITMF as _


@view_action('help_action', 'wiki')
def action_manual(context, request, va, **kw):
    api = kw['api']
    return u"""<li><a href="http://wiki.voteit.se" target="_blank">%s</a></li>""" % (api.translate(_(u"VoteIT Manual")),)

@view_action('help_action', 'contact', title = _(u"Contact moderator"))
def action_contact(context, request, va, **kw):
    api = kw['api']
    if api.meeting:
        return u"""<li><a href="%s">%s</a></li>""" % (request.resource_url(api.meeting, 'contact'),
                                                                           api.translate(va.title),)
    return u""

@view_action('help_action', 'lost_password', title = _(u"Lost your password?"))
def action_lost_password(context, request, va, **kw):
    api = kw['api']
    if api.userid:
        return u""
    return u"""<li><a href="%s">%s</a></li>""" % (request.resource_url(api.root, 'request_password'),
                                                                       api.translate(va.title),)

@view_action('help_action', 'support', title = _(u"Support"))
def action_support(context, request, va, **kw):
    api = kw['api']
    context = api.meeting and api.meeting or api.root
    return """<li><a href="%s">%s</a></li>""" % (request.resource_url(context, 'support'),
                                                 api.translate(va.title),)
