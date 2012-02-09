from pyramid.renderers import render
from pyramid.url import resource_url
from betahaus.viewcomponent import view_action
from betahaus.pyracont.factories import createSchema

from voteit.core import VoteITMF as _
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_send
from voteit.core.views.help import HelpView


@view_action('main', 'help_actions')
def help_actions(context, request, va, **kw):
    api = kw['api']
    response = {}
    response['api'] = api
    return render('../templates/snippets/help_actions.pt', response, request = request)


@view_action('help_action', 'wiki')
def action_wiki(context, request, va, **kw):
    api = kw['api']
    return """<li><a class="buttonize" href="http://wiki.voteit.se" target="_blank">%s</a></li>""" % (api.translate(_(u"VoteIT Wiki")),)


@view_action('help_action', 'contact')
def action_contact(context, request, va, **kw):
    api = kw['api']
    if api.meeting:
        return """<li><a class="tab buttonize" href="#help-tab-contact">%s</a></li>""" % (api.translate(_(u"Contact")),)
    return ""


@view_action('main', 'help_tabs')
def help_tabs(context, request, va, **kw):
    api = kw['api']
    response = {}
    response['api'] = api
    return render('../templates/snippets/help_tabs.pt', response, request = request)


@view_action('help_tab', 'contact')
def tab_contact(context, request, va, **kw):
    api = kw['api']
    if api.meeting:
        hw = HelpView(api.meeting, request)
        return """<div id="help-tab-contact" class="tab">%s</div>""" % (hw.contact(),)
    return ""