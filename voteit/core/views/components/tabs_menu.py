# from betahaus.viewcomponent import view_action
# from betahaus.viewcomponent.interfaces import IViewGroup
# from pyramid.renderers import render
# 
# from voteit.core import VoteITMF as _
# from voteit.core.security import MODERATE_MEETING
# from voteit.core.security import MANAGE_GROUPS
# 
# 
# @view_action('tabs', 'manage_agenda', permission = MODERATE_MEETING)
# @view_action('tabs', 'manage_tickets', permission = MANAGE_GROUPS)
# def render_tabs_menu(context, request, va, **kw):
#     """ Render tabs from a specific view group. This is to make the tabs pluggable. """
#     view_group = request.registry.queryUtility(IViewGroup, name = va.name)
#     if not view_group:
#         return u""
#     tabs = [x(context, request, **kw) for x in view_group.values()]
#     if not tabs:
#         return u""
#     response = {'api': kw['api'], 'tabs': tabs}
#     return render('templates/tabs_menu.pt', response, request = request)
# 
# @view_action('manage_agenda', 'manage_agenda_items', link = u'manage_agenda_items',
#              title = _(u"Manage"))
# @view_action('manage_agenda', 'order_agenda_items', link = u'order_agenda_items',
#              title = _(u"Order"))
# @view_action('manage_agenda', 'agenda_templates', link = u'agenda_templates',
#              title = _(u"Agenda templates"))
# @view_action('manage_tickets', 'add_tickets', link = u'add_tickets',
#              title = _(u"Invite participants"))
# @view_action('manage_tickets', 'add_permission', link = u'add_permission',
#              title = _(u"Add existing user"))
# @view_action('manage_tickets', 'manage_tickets', link = u'manage_tickets',
#              title = _(u"Manage invitations"))
# def generic_tab_any_querystring(context, request, va, **kw):
#     """ A generic tab function that can be decorated to create tabs with context as its root. """
#     api = kw['api']
#     url = request.resource_url(context, va.kwargs['link'])
#     css_classes = request.path_url == url and 'selected' or ''
#     return u"""<li class="%(css_classes)s"><a href="%(url)s">%(title)s</a></li>""" % {'css_classes': css_classes,
#                                                                        'title': api.translate(va.title),
#                                                                        'url': url}
# 
# @view_action('manage_agenda', 'add_agenda_item', title = _(u"Add agenda item"))
# def add_agenda_item(context, request, va, **kw):
#     """ Specific tab for adding an agenda item. """
#     api = kw['api']
#     url = request.resource_url(api.meeting, 'add', query = {'content_type': 'AgendaItem'})
#     css_classes = request.url == url and 'selected' or ''
#     return u"""<li class="%(css_classes)s"><a href="%(url)s">%(title)s</a></li>""" % {'css_classes': css_classes,
#                                                                        'title': api.translate(va.title),
#                                                                        'url': url}
