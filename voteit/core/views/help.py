from arche.interfaces import IRoot
from arche.views.base import BaseView
from betahaus.viewcomponent import view_action
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config

from voteit.core import _
from voteit.core.models.interfaces import IMeeting
from voteit.core.security import VIEW


@view_config(context=IRoot,
             name='_help_menu',
             permission=NO_PERMISSION_REQUIRED,
             renderer='voteit.core:templates/menus/help.pt')
@view_config(context=IMeeting,
             name='_help_menu',
             permission=VIEW,
             renderer='voteit.core:templates/menus/help.pt')
class HelpView(BaseView):

    def __call__(self):
        return {}


# @view_action('help_action', 'manual', title = _("VoteIT Manual"))
# def action_manual(context, request, va, **kw):
#     title = request.localizer.translate(va.title)
#     return """<li><a href="http://manual.voteit.se" target="_blank">%s</a></li>""" % title


@view_action('help_action', 'contact', title = _("Contact moderator"))
def action_contact(context, request, va, **kw):
    if request.meeting:
        return """<li><a href="%s">%s</a></li>""" % (request.resource_url(request.meeting, 'contact'),
                                                     request.localizer.translate(va.title),)


@view_action('help_action', 'lost_password', title = _("Lost your password?"))
def action_lost_password(context, request, va, **kw):
    if not request.authenticated_userid:
        return u"""<li><a href="%s">%s</a></li>""" % (request.resource_url(request.root, 'recover_password'),
                                                      request.localizer.translate(va.title),)


@view_action('help_action', 'support', title = _("Support"))
def action_support(context, request, va, **kw):
    context = request.meeting and request.meeting or request.root
    return """<li><a href="%s">%s</a></li>""" % (request.resource_url(context, 'support'),
                                                 request.localizer.translate(va.title),)
