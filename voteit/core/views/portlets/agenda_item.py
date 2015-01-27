""" Portlets that by default will be rendered within the Agenda Item view.
    They can be rearranged or disabled by changing them within the meeting context.
"""
from __future__ import unicode_literals

from arche.portlets import PortletType
from pyramid.renderers import render
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
import colander
from arche.views.base import BaseView
from repoze.catalog.query import Eq, NotAny, Any

from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.fanstaticlib import ai_portlet_js, data_loader
from voteit.core import _




class ProposalsPortlet(PortletType):
    name = "ai_proposals"
    schema_factory = None
    title = _("Agenda Item: Proposals listing")

    def render(self, context, request, view, **kwargs):
        if IAgendaItem.providedBy(context):
            data_loader.need()
            response = {'portlet': self.portlet, 'view': view}
            return render("voteit.core:views/templates/portlets/proposals.pt",
                          response, request = request)


class ProposalsInline(BaseView):
    
    def __call__(self):
        query = {
            'path': resource_path(self.context),
            'type_name': 'Proposal',
            'sort_index': 'created',
             }
        #query = Eq('path', resource_path(self.context)) &\
        #        Eq('type_name', 'Proposal') #&\
                #NotAny('uid', shown_uids)
    
        tag = self.request.GET.get('tag', None)
        if tag:
            #Only apply tag limit for things that aren't polls.
            #This is a safegard against user errors
            #query &= Any('tags', (tag, ))
            query['tags'] = tag
            
        # build query string and remove tag
        #clear_tag_query = self.request.GET.copy()
        #if 'tag' in clear_tag_query:
        #    del clear_tag_query['tag']
    
        #hide_retracted = self.request.meeting.get_field_value('hide_retracted', False)
        #hide_unhandled = self.request.meeting.get_field_value('hide_unhandled_proposals', False)
        #hidden_states = []
        #if hide_retracted:
        #    hidden_states.append('retracted')
        #if hide_unhandled:
        #    hidden_states.append('unhandled')
        #if hidden_states:
        #    query &= NotAny('workflow_state', hidden_states)
        response = {}
        response['contents'] = self.catalog_search(resolve = True, **query)
        #count, docids = .root.catalog.query(query, sort_index='created')
        #get_metadata = api.root.catalog.document_map.get_metadata
        #results = [get_metadata(x) for x in docids]
#         hidden_proposals = []
#         if hidden_states:
#             query = Eq('path', resource_path(context)) &\
#                     Eq('content_type', 'Proposal') &\
#                     NotAny('uid', shown_uids) &\
#                     Any('workflow_state', hidden_states)
#             if tag:
#                 query &= Any('tags', (tag, ))
#             count, docids = api.root.catalog.query(query, sort_index='created')
#             hidden_proposals = [get_metadata(x) for x in docids]
    
#         response['clear_tag_url'] = self.request.resource_url(self.context, query=clear_tag_query)
#         response['proposals'] = tuple(results)
#         response['hidden_proposals'] = tuple(hidden_proposals)
#         response['tag'] = tag
#         response['api'] = api 
#         response['polls'] = polls
        return response

# states = ('ongoing', 'upcoming', 'closed', 'private')
# 
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
    config.add_portlet_slot('agenda_item', title = _("Agenda Item portlets"), layout = 'vertical')
    config.add_portlet(ProposalsPortlet)
    config.add_view(ProposalsInline,
                    name = '__ai_proposals__',
                    context = IAgendaItem,
                    renderer = 'voteit.core:views/templates/portlets/proposals_inline.pt')

