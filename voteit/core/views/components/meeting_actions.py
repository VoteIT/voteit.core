from betahaus.viewcomponent import view_action
from pyramid.renderers import render

from voteit.core.security import MANAGE_SERVER
from voteit.core.security import MODERATE_MEETING
from voteit.core.security import VIEW
from voteit.core.security import MANAGE_GROUPS
from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IAccessPolicy


#FIXME:
#@view_action('admin_menu', 'moderators_emails', title = _(u"Moderators emails"), link = "moderators_emails")
#FIXME: @view_action('admin_menu', 'agenda_templates', title = _(u"Agenda templates"), link = "agenda_templates")
#@view_action('admin_menu', 'layout', title = _(u"Layout"), link = "layout") Use this?
def generic_root_menu_link(context, request, va, **kw):
    """ This is for simple menu items for the root """
    api = kw['api']
    url = api.resource_url(api.root, request) + va.kwargs['link']
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))
