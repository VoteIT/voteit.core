from __future__ import unicode_literals

from arche.interfaces import IRoot
from arche.interfaces import IUser
from arche.portlets import PortletType
from pyramid.renderers import render
from pyramid.traversal import resource_path
from pyramid.traversal import find_resource

from voteit.core.models.interfaces import IMeeting
from voteit.core.security import VIEW
from voteit.core import _


class MeetingListingPortlet(PortletType):
    name = "meeting_list"
    title = _("Meeting list")

    def render(self, context, request, view, **kwargs):
        if request.authenticated_userid and (IRoot.providedBy(context) or IUser.providedBy(context)):
            response = {'title': _("Meetings"),
                        'portlet': self.portlet,
                        'portlet_cls': "portlet-%s" % self.name,
                        'view': view,
                        'item_count_for': self.item_count_for,
                        'state_titles': request.get_wf_state_titles(IMeeting, 'Meeting'),
                        'get_meetings': _get_meetings}
            return render("voteit.core:templates/portlets/meeting_list.pt",
                          response,
                          request = request)

    def item_count_for(self, request, context, type_name, unread = False):
        query = {'path': resource_path(context),
                 'type_name': type_name}
        if unread:
            query['unread'] = request.authenticated_userid
        return request.root.catalog.search(**query)[0].total

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
