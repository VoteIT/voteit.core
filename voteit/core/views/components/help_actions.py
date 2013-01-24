from pyramid.renderers import render
from betahaus.viewcomponent import view_action

from voteit.core import VoteITMF as _


@view_action('help_action', 'wiki')
def action_wiki(context, request, va, **kw):
    api = kw['api']
    return """<li><a href="http://wiki.voteit.se" target="_blank">%s</a></li>""" % (api.translate(_(u"VoteIT Manual")),)


@view_action('help_action', 'contact')
def action_contact(context, request, va, **kw):
    api = kw['api']
    if api.meeting:
        return """<li><a href="%s">%s</a></li>""" % (request.resource_url(api.meeting, 'contact'),
                                                                           api.translate(_(u"Contact")),)
    return ""
