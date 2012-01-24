from pyramid.renderers import render
from pyramid.url import resource_url
from betahaus.viewcomponent import view_action

from voteit.core import VoteITMF as _


@view_action('main', 'help_actions')
def help_actions(context, request, va, **kw):
    """ The main global actions view component which will render the rest of them. """
    api = kw['api']
    response = {}
    response['api'] = api
    return render('../templates/snippets/help_actions.pt', response, request = request)


@view_action('help_action', 'wiki')
def action_wiki(context, request, va, **kw):
    api = kw['api']
    return """<li><a href="http://wiki.voteit.se" class="buttonize" target="_blank">%s</a></li>""" % (api.translate(_(u"VoteIT Wiki")))


@view_action('help_action', 'contact')
def action_contact(context, request, va, **kw):
    api = kw['api']
    if api.meeting:
        link = resource_url(api.meeting, request) + "contact"
        return """<li><a id="contact" class="tab buttonize" href="%s">%s</a></li>""" % (link, api.translate(_(u"Contcat")))
        
    return ""