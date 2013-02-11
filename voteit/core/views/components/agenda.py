from betahaus.viewcomponent import view_action
from voteit.core import VoteITMF as _


@view_action('manage_agenda', 'manage_agenda_items', link = 'manage_agenda_items',
             title = _(u"Manage"))
@view_action('manage_agenda', 'order_agenda_items', link = 'order_agenda_items',
             title = _(u"Order"))
@view_action('manage_agenda', 'agenda_templates', link = 'agenda_templates',
             title = _(u"Agenda templates"))
def agenda_menu_items(context, request, va, **kw):
    """ Manage agenda tabs, visible on the manage agenda screen. """
    api = kw['api']
    url = request.resource_url(api.meeting, va.kwargs['link'])
    css_classes = request.url == url and 'selected' or ''
    return u"""<li class="%(css_classes)s"><a href="%(url)s">%(title)s</a></li>""" % {'css_classes': css_classes,
                                                                       'title': api.translate(va.title),
                                                                       'url': url}
