from __future__ import unicode_literals

from arche.views.base import BaseView
from betahaus.viewcomponent.interfaces import IViewGroup
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.traversal import resource_path
from pyramid.view import view_config
from pyramid.view import view_defaults
from repoze.catalog.query import Eq, NotAny, Any

from voteit.core import VoteITMF as _
from voteit.core import _
from voteit.core import security
from voteit.core.fanstaticlib import unread_js
from voteit.core.helpers import get_docids_to_show
from voteit.core.models.interfaces import IAgendaItem


class AgendaItemView(BaseView):

    def __call__(self):
        unread_js.need()
        return {}


class AIToggleBlockView(BaseView):

    def __call__(self):
        """ Toggle wether discussion or proposals are allowed. """
        discussion_block = self.request.GET.get('discussion_block', None)
        proposal_block = self.request.GET.get('proposal_block', None)
        if discussion_block is not None:
            val = bool(int(discussion_block))
            self.context.set_field_value('discussion_block', val)
        if proposal_block is not None:
            val = bool(int(proposal_block))
            self.context.set_field_value('proposal_block', val)
        self.flash_messages.add(_(u"Status changed - note that workflow state also matters."))
        url = self.request.resource_url(self.context)
        if self.request.referer:
            url = self.request.referer
         #FIXME: This should be done via javascript instead
        return HTTPFound(location=url)


@view_defaults(context = IAgendaItem, permission = security.VIEW, renderer = 'json')
class AgendaContentsJSON(BaseView):

    def add_directives(self, view_group):
        vg = self.request.registry.getUtility(IViewGroup, name = view_group)
        directives = {}
        directives['[data-docid]@data-docid'] = 'obj.docid'
        for va in vg.values():
            directives.update( va.kwargs.get('directives', {}) )
        return directives

    @view_config(name = 'ai_proposals.json')
    def proposals_data(self):
        hidden = bool(self.request.GET.get('hidden', False))
        query = Eq('path', resource_path(self.context)) & Eq('type_name', 'Proposal')
        if hidden:
            query &= Any('workflow_state', tuple(self.request.meeting.hide_proposal_states))
        else:
            query &= NotAny('workflow_state', tuple(self.request.meeting.hide_proposal_states))
        response = {}
        docids = tuple(self.catalog_query(query, sort_index = 'created'))
        unread_docids = tuple(self.catalog_query(query & Eq('unread', self.request.authenticated_userid)))
        response['contents'] = []
        response['directives'] = self.add_directives('proposal_json')
        for docid in docids:
            result = {'docid': docid, 'unread': docid in unread_docids}
            for obj in self.resolve_docids(docid):
                result.update(self.render_view_group('proposal_json', context = obj, as_type = 'dict', empty_val = ''))
            response['contents'].append(result)
        response.update(self.get_filter())
        return response

    @view_config(name = 'ai_discussion_posts.json')
    def discussion_data(self):
        query = {}
        query['limit'] = 10
        if self.request.GET.get('previous', False):
            query['limit'] = 0
            query['end_before'] = int(self.request.GET.get('end_before'))
        if self.request.GET.get('next', False):
            query['start_after'] = int(self.request.GET.get('start_after'))
        response = get_docids_to_show(self.context, self.request, 'DiscussionPost', **query)
        response['directives'] = self.add_directives('discussion_post_json')
        response['contents'] = []
        for docid in response['batch']:
            result = {'docid': docid, 'unread': docid in response['unread']}
            for obj in self.resolve_docids(docid):
                result.update(self.render_view_group('discussion_post_json',
                                                     context = obj,
                                                     as_type = 'dict',
                                                     empty_val = ''))
            response['contents'].append(result)
        if response['previous'] and response['batch']:
            end_before = response['batch'][0]
            msg = _("Show ${num} previous post(s)",
                    mapping = {'num': len(response['previous'])})
            response['load_previous_msg'] = self.request.localizer.translate(msg)
            response['load_previous_url'] = self.request.resource_url(self.context, 'ai_discussion_posts.json',
                                                                      query = {#'tag': query['tags'],
                                                                               'previous': 1,
                                                                               'end_before': end_before})
        if response['over_limit'] and response['batch']:
            start_after = response['batch'][-1]
            msg = _("Load more (from ${num} unread)",
                    mapping = {'num': len(response['over_limit'])})
            response['load_next_msg'] = self.request.localizer.translate(msg)
            response['load_next_url'] = self.request.resource_url(self.context, 'ai_discussion_posts.json',
                                                                  query = {#'tag': query['tags'],
                                                                           'next': 1,
                                                                           'start_after': start_after})
        response.update(self.get_filter())
        return response

    def get_filter(self):
        """ Figure out which docids that should be visible."""
        query = Eq('path', resource_path(self.context)) & Any('type_name', ['Proposal', 'DiscussionPost'])
        tags = set(self.request.GET.getall('tag'))
        if not tags:
            tags.update(self.request.GET.getall('tag[]')) #jQuery bs...
        if not self.request.is_xhr:
            url = self.request.resource_url(self.context, query = {'tag': tags})
            return HTTPFound(location = url)
        if tags:
            tags = [x.lower() for x in tags]
            query &= Any('tags', tags)
        else:
            tags = []#sets don't work with json
        response = {'show_docids': list(self.catalog_query(query)),
                    'tags': tags}
        if tags:
            response['filter_msg'] = render('voteit.core:templates/snippets/filter_msg.pt', {}, request = self.request)
        return response

    @view_config(name = 'ai_filter.json')
    def ai_filter(self):
        return self.get_filter()


def includeme(config):
    config.add_view(AgendaItemView,
                    context = IAgendaItem,
                    renderer = "voteit.core:templates/agenda_item.pt",
                    permission = security.VIEW)
    config.add_view(AIToggleBlockView,
                    context = IAgendaItem,
                    name = "_toggle_block",
                    permission = security.MODERATE_MEETING)
