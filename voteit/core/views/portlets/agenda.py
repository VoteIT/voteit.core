from __future__ import unicode_literals

from arche import _
from arche.portlets import PortletType
from pyramid.renderers import render
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
import colander

from voteit.core.models.interfaces import IMeeting
from voteit.core.fanstaticlib import ai_portlet_js


class AgendaPortlet(PortletType):
    name = "agenda"
    schema_factory = None
    title = _("Agenda")

    def render(self, context, request, view, **kwargs):
        meeting = find_interface(context, IMeeting)
        if meeting:
            ai_portlet_js.need()
            response = {'title': self.title,
                        'portlet': self.portlet,
                        'meeting': meeting,
                        'data_url': request.resource_url(meeting, '__agenda_items__.json')}
            return render("voteit.core:views/templates/portlets/agenda.pt",
                          response,
                          request = request)



states = ('ongoing', 'upcoming', 'closed', 'private')

def jsondata_agenda(context, request):
    root = find_root(context)
    path = resource_path(context)
    results = []
    for state in states:
        state_res = []
        for docid in root.catalog.search(path = path, type_name = 'AgendaItem', workflow_state = state, sort_index = 'order')[1]:
            try:
                meta = dict(root.document_map.get_metadata(docid))
            except KeyError:
                meta = {}
            state_res.append( meta )
        results.append({'state': state, 'state_ais': state_res}) 
    return results


def includeme(config):
    config.add_view(jsondata_agenda, name = '__agenda_items__.json', context = IMeeting, renderer = 'json')
    config.add_portlet(AgendaPortlet)
