from __future__ import unicode_literals

from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core import _

from voteit.core.models.interfaces import IMeeting
from voteit.core import _
from voteit.core.security import VIEW
from betahaus.viewcomponent import render_view_group


@view_action('nav_right', 'help',
             title = _("Help"),
             priority = 5,
             renderer = 'voteit.core:templates/snippets/help_menu.pt')
def polls_menu(context, request, va, **kw):
    response = {}
    response['menu_html'] = render_view_group(context, request, 'help_action')
    return render(va.kwargs['renderer'], response, request = request)


@view_action('help_action', 'manual', title = _(u"VoteIT Manual"))
def action_manual(context, request, va, **kw):
    title = request.localizer.translate(va.title)
    return """<li><a href="http://manual.voteit.se" target="_blank">%s</a></li>""" % title

@view_action('help_action', 'contact', title = _(u"Contact moderator"), containment = IMeeting)
def action_contact(context, request, va, **kw):
    return """<li><a href="%s">%s</a></li>""" % (request.resource_url(request.meeting, 'contact'),
                                                 request.localizer.translate(va.title),)

@view_action('help_action', 'lost_password', title = _(u"Lost your password?"))
def action_lost_password(context, request, va, **kw):
    if not request.authenticated_userid:
        return u"""<li><a href="%s">%s</a></li>""" % (request.resource_url(request.root, 'recover_password'),
                                                      request.localizer.translate(va.title),)

@view_action('help_action', 'support', title = _(u"Support"))
def action_support(context, request, va, **kw):
    context = request.meeting and request.meeting or request.root
    return """<li><a href="%s">%s</a></li>""" % (request.resource_url(context, 'support'),
                                                 request.localizer.translate(va.title),)
