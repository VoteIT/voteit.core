from __future__ import unicode_literals

from arche.portlets import PortletType
from arche.views.base import BaseView
from pyramid.renderers import render
from pyramid.traversal import resource_path

from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core import _
from voteit.core.fanstaticlib import data_loader


class AgendaPortlet(PortletType):
    name = "agenda"
    schema_factory = None
    title = _("Agenda")
    tpl = "voteit.core:templates/portlets/agenda.pt"

    def load_url(self, request, ai_name):
        return request.resource_url(request.meeting, '__agenda_items__', query = {'ai_name': ai_name})

    def render(self, context, request, view, **kwargs):
        if request.meeting:
            data_loader.need()
            ai_name = IAgendaItem.providedBy(context) and context.__name__ or ''
            response = {'title': self.title,
                        'portlet': self.portlet,
                        'view': view,
                        'load_url': self.load_url(request, ai_name)}
            return render(self.tpl,
                          response,
                          request = request)


class AgendaPortletFixed(AgendaPortlet):
    name = "agenda_fixed"
    title = _("Fixed agenda")
    tpl = "voteit.core:templates/portlets/agenda_fixed.pt"

    def load_url(self, request, ai_name):
        return request.resource_url(request.meeting, '__agenda_fixed_inline__', query = {'ai_name': ai_name})


class AgendaInlineView(BaseView):
    unread_types = ('Proposal', 'DiscussionPost')

    def __call__(self):
        response = {}
        states = ['ongoing', 'upcoming', 'closed']
        if self.request.is_moderator:
            states.append('private')
        response['states'] = states
        response['state_titles'] = self.request.get_wf_state_titles(IAgendaItem, 'AgendaItem')
        response['meeting_path'] = self.meeting_path = resource_path(self.request.meeting)
        self.ai_name = self.request.GET.get('ai_name', None)
        return response

    def get_ais(self, state):
        catalog = self.request.root.catalog
        docids = catalog.search(path = self.meeting_path,
                                    type_name = 'AgendaItem',
                                    workflow_state = state)[1]
        #Don't check permission here, assume permission check done before
        results = self.request.resolve_docids(docids, perm=None)
        ai_order = self.context.order
        def _sorter(ai):
            try:
                return ai_order.index(ai.__name__)
            except (ValueError, KeyError):
                return len(ai_order)
        return sorted(results, key=_sorter)

    def count_types(self, ai):
        results = {}
        userid = self.request.authenticated_userid
        rn = self.request.get_read_names(ai)
        for utype in self.unread_types:
            total = rn.get_type_count(utype)
            results[utype] = {'total': total, 'unread': total-rn.get_read_type(utype, userid)}
        results['Poll'] = {'total': rn.get_type_count('Poll')}
        return results


def includeme(config):
    config.add_portlet(AgendaPortlet)
    config.add_portlet(AgendaPortletFixed)
    config.add_view(AgendaInlineView,
                    name = '__agenda_items__',
                    context = IMeeting,
                    renderer = 'voteit.core:templates/portlets/agenda_inline.pt')
    config.add_view(AgendaInlineView,
                    name = '__agenda_fixed_inline__',
                    context = IMeeting,
                    renderer = 'voteit.core:templates/portlets/agenda_inline_fixed.pt')
