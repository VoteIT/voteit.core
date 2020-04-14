from __future__ import unicode_literals

from arche.interfaces import IRoot
from arche.interfaces import IUser
from arche.portlets import PortletType
from pyramid.renderers import render
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource
from repoze.catalog.query import Eq

from voteit.core.models.interfaces import IMeeting
from voteit.core.security import VIEW
from voteit.core import _


_meeting_states = ('ongoing', 'upcoming', 'closed')


class MeetingListingPortlet(PortletType):
    name = "meeting_list"
    title = _("Meeting list")
    tpl = "voteit.core:templates/portlets/meeting_list.pt"

    def visible(self, context, request, view, **kwargs):
        if request.authenticated_userid and (IRoot.providedBy(context) or IUser.providedBy(context)):
            return True
        return False

    def render(self, context, request, view, **kwargs):

        def item_count_for(meeting, type_name):
            query = Eq('path', resource_path(meeting)) & Eq('type_name', type_name)
            return request.root.catalog.query(query)[0].total

        if request.authenticated_userid and (IRoot.providedBy(context) or IUser.providedBy(context)):
            meetings = {}
            collapse = {}
            for state in _meeting_states:
                meetings[state] = _get_meetings(request, state = state)
                collapse[state] = False
            if len(meetings['ongoing']) + len(meetings['upcoming']) > 9:
                collapse['closed'] = True
            if len(meetings['ongoing']) > 9:
                collapse['upcoming'] = True
            response = {'title': _("Meetings"),
                        'portlet': self.portlet,
                        'portlet_cls': "portlet-%s" % self.name,
                        'view': view,
                        'meetings': meetings,
                        'collapse': collapse,
                        'meeting_states': _meeting_states,
                        'item_count_for': item_count_for,
                        'state_titles': request.get_wf_state_titles(IMeeting, 'Meeting'),}
            return render(self.tpl,
                          response,
                          request = request)


def _get_meetings(request, state = 'ongoing', sort_index = 'sortable_title'):
    root = request.root
    results = []
    for docid in root.catalog.search(type_name = 'Meeting',
                                     workflow_state = state,
                                     sort_index = sort_index)[1]:
        path = root.document_map.address_for_docid(docid)
        obj = find_resource(root, path)
        if request.has_permission(VIEW, obj):
            results.append(obj)
    return results


def includeme(config):
    config.add_portlet(MeetingListingPortlet)
