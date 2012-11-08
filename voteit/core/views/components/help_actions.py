from pyramid.renderers import render
from pyramid.url import resource_url
from betahaus.viewcomponent import view_action

from voteit.core import VoteITMF as _
from voteit.core.fanstaticlib import jquery_form 


@view_action('main', 'help_actions')
def help_actions(context, request, va, **kw):
    api = kw['api']
    response = {}
    response['api'] = api
    
    # this is needed for the forms to work
    jquery_form.need()
    
    return render('../templates/snippets/help_actions.pt', response, request = request)


@view_action('help_action', 'wiki')
def action_wiki(context, request, va, **kw):
    api = kw['api']
    return """<li><a class="buttonize" href="http://wiki.voteit.se" target="_blank">%s</a></li>""" % (api.translate(_(u"VoteIT Wiki")),)


@view_action('help_action', 'contact')
def action_contact(context, request, va, **kw):
    api = kw['api']
    if api.meeting:
        return """<li><a class="tab buttonize" href="%s">%s</a></li>""" % (resource_url(api.meeting, request)+"contact", api.translate(_(u"Contact")),)
    return ""
