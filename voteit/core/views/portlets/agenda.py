from __future__ import unicode_literals

from arche.portlets import PortletType
from pyramid.renderers import render
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
import colander
from arche.views.base import BaseView

from voteit.core.models.interfaces import IMeeting
from voteit.core import _
from voteit.core.fanstaticlib import data_loader

class AgendaPortlet(PortletType):
    name = "agenda"
    schema_factory = None
    title = _("Agenda")

    def render(self, context, request, view, **kwargs):
        meeting = find_interface(context, IMeeting)
        if meeting:
            data_loader.need()
            response = {'title': self.title,
                        'portlet': self.portlet,
                        'view': view,
                        'load_url': request.resource_url(meeting, '__agenda_items__')}
            return render("voteit.core:views/templates/portlets/agenda.pt",
                          response,
                          request = request)


class AgendaInlineView(BaseView):

    def __call__(self):
        response = {}
        response['states'] = ('ongoing', 'upcoming', 'closed', 'private')
        response['meeting'] = self.request.meeting
        return response

    def get_ais(self, state):
        path = resource_path(self.context)
        results = []
        catalog = self.request.root.catalog
        for docid in catalog.search(path = path,
                                    type_name = 'AgendaItem',
                                    workflow_state = state,
                                    sort_index = 'order')[1]:
            try:
                meta = dict(self.request.root.document_map.get_metadata(docid))
            except KeyError:
                meta = {}
            results.append(meta)
        return results

# def jsondata_agenda(context, request):
#     root = find_root(context)
#     path = resource_path(context)
#     results = []
#     for state in states:
#         state_res = []
#         for docid in root.catalog.search(path = path, type_name = 'AgendaItem', workflow_state = state, sort_index = 'order')[1]:
#             try:
#                 meta = dict(root.document_map.get_metadata(docid))
#             except KeyError:
#                 meta = {}
#             state_res.append( meta )
#         results.append({'state': state, 'state_ais': state_res}) 
#     return results


def includeme(config):
    config.add_view(AgendaInlineView,
                    name = '__agenda_items__',
                    context = IMeeting,
                    renderer = 'voteit.core:views/templates/portlets/agenda_inline.pt')
    config.add_portlet(AgendaPortlet)
