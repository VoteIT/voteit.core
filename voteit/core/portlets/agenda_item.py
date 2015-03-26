""" Portlets that by default will be rendered within the Agenda Item view.
    They can be rearranged or disabled by changing them within the meeting context.
"""
from __future__ import unicode_literals
from decimal import Decimal
from copy import copy

from arche.portlets import PortletType
from arche.utils import generate_slug
from arche.views.base import BaseView
from arche.views.base import DefaultAddForm
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.traversal import resource_path
from repoze.catalog.query import Eq, NotAny, Any

from voteit.core import _
from voteit.core import security
from voteit.core.fanstaticlib import data_loader
from voteit.core.helpers import get_docids_to_show
from voteit.core.helpers import tags2links
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.schemas.meeting import AgendaItemProposalsPortletSchema

#FIXME: Loading required resources for inline forms is still a problem.


class ListingPortlet(PortletType):
    schema_factory = None

    def render(self, context, request, view, **kwargs):
        if IAgendaItem.providedBy(context):
            query = {}
            tag = request.GET.get('tag', None)
            if tag:
                query['tag'] = tag
            url = request.resource_url(context, self.view_name, query = query)
            response = {'portlet': self.portlet, 'view': view, 'load_url': url}
            return render(self.template, response, request = request)


class ProposalsPortlet(ListingPortlet):
    name = "ai_proposals"
    title = _("Agenda Item: Proposals listing")
    template = "voteit.core:templates/portlets/proposals.pt"
    view_name = '__ai_proposals__'
    schema_factory = AgendaItemProposalsPortletSchema

    def render(self, context, request, view, **kwargs):
        if IAgendaItem.providedBy(context):
            data_loader.need()
            query = {}
            tags = request.GET.getall('tag')
            if tags:
                query['tag'] = tags
            query['hide'] = tuple(self.portlet.settings.get('hide_proposal_states', ()))
            url = request.resource_url(context, self.view_name, query = query)
            response = {'portlet': self.portlet, 'view': view, 'load_url': url}
            return render(self.template, response, request = request)


class DiscussionsPortlet(ListingPortlet):
    name = "ai_discussions"
    title = _("Agenda Item: Discussions listing")
    template = "voteit.core:templates/portlets/discussions.pt"
    view_name = '__ai_discussions__'


class PollsPortlet(ListingPortlet):
    name = "ai_polls"
    title = _("Agenda Item: Polls listing")
    template = "voteit.core:templates/portlets/polls.pt"
    view_name = '__ai_polls__'


class ProposalsInline(BaseView):
    
    def __call__(self):
        response = {}
        query = Eq('path', resource_path(self.context)) &\
                Eq('type_name', 'Proposal')
        tags = self.request.GET.getall('tag')
        if tags:
            query &= Any('tags', tags)
        hide = self.request.GET.getall('hide')
        load_hidden = self.request.GET.get('load_hidden', False)
        if load_hidden:
            #Only load data previously hidden
            if hide:
                query &= Any('workflow_state', hide)
        else:
            invert_hidden = copy(query)
            #Normal operation, keep count of hidden
            if hide:
                invert_hidden &= Any('workflow_state', hide)
                query &= NotAny('workflow_state', hide)
        
        response['docids'] = tuple(self.catalog_query(query, sort_index = 'created'))
        response['unread_docids'] = tuple(self.catalog_query(query & Eq('unread', self.request.authenticated_userid), sort_index = 'created'))
        response['contents'] = self.resolve_docids(response['docids']) #A generator
        if not load_hidden:
            response['hidden_count'] = self.request.root.catalog.query(invert_hidden)[0].total
            get_query = {'tag': tags, 'load_hidden': 1, 'hide': hide}
            response['load_hidden_url'] = self.request.resource_url(self.context, self.request.view_name, query = get_query)
        else:
            response['hidden_count'] = False
        return response


class DiscussionsInline(BaseView):
    
    def __call__(self):
        """ Loading procedure of discussion posts:
            If nothing specific is set, limit loading to the next 5 unread.
            If there aren't 5 unread, fetch the 5 last posts.
            If there are more unread than 5, create a link to load more.
            
        """
        query = {}
        query['tags'] = self.request.GET.getall('tag')
        query['limit'] = 5
        if self.request.GET.get('previous', False):
            query['limit'] = 0
            query['end_before'] = int(self.request.GET.get('end_before'))
        if self.request.GET.get('next', False):
            query['start_after'] = int(self.request.GET.get('start_after'))
        response = get_docids_to_show(self.context, self.request, 'DiscussionPost', **query)
        response['contents'] = self.resolve_docids(response['batch']) #Generator
        if response['previous'] and response['batch']:
            end_before = response['batch'][0]
            response['load_previous_url'] = self.request.resource_url(self.context, '__ai_discussions__',
                                                                      query = {'tag': query['tags'],
                                                                               'previous': 1,
                                                                               'end_before': end_before})
        if response['over_limit'] and response['batch']:
            start_after = response['batch'][-1]
            response['load_next_url'] = self.request.resource_url(self.context, '__ai_discussions__',
                                                                  query = {'tag': query['tags'],
                                                                           'next': 1,
                                                                           'start_after': start_after})
        return response

#         
#         last_shown_docid = None #FIXME
#         query = "path == '%s' and type_name == 'DiscussionPost'" % resource_path(self.context)
#         tags = self.request.GET.getall('tag')
#         if tags:
#             query += " and tags in any(%s)" % tags
#         unread_query = "unread == '%s' and %s" % (self.request.authenticated_userid, query)
#         query += " and unread != '%s'" % self.request.authenticated_userid
#         showing_docids = []
#         over_limit_unread = []
#         previous = []
#         limit = 5 #Set another way?
#         #Fetch <limit> number of docids and insert them in shown_docids
#         #If there are more unread, add them to over_limit_unread
#         unread_docids = list(self.catalog_query(unread_query, sort_index = 'created'))
#         docids_pool = list(self.catalog_query(query, sort_index = 'created'))
        
            
        
#         
#         for docid in unread_docids:
#             if len(showing_docids) < limit:
#                 showing_docids.append(docid)
#             else:
#                 over_limit_unread.append(docid)
#         #If there aren't enough shown docids, walk through them in reverse order.
#         query += " and unread != '%s'" % self.request.authenticated_userid
#         pool = self.catalog_query(query, sort_index = 'created', reverse = True)
#         for docid in pool:
#             if len(showing_docids) < limit:
#                 showing_docids.insert(0, docid)
#             else:
#                 previous.append(docid)
#         response = {}
#         response['unread_docids'] = unread_docids
#         response['docids'] = showing_docids
#         response['contents'] = self.resolve_docids(showing_docids)
#         response['over_limit_unread'] = over_limit_unread
#         response['previous'] = previous
#         return response

    


class PollsInline(BaseView):
    
    def __call__(self):
        query = {
            'path': resource_path(self.context),
            'type_name': 'Poll',
            'sort_index': 'created',}
        response = {}
        response['contents'] = tuple(self.catalog_search(resolve = True, **query))
        response['vote_perm'] = security.ADD_VOTE
        return response

    def get_proposal_tag_links(self, poll):
        text = ""
        for prop in poll.get_proposal_objects():
            text += "#%s " % prop.aid
        return tags2links(text)

    def get_voted_estimate(self, poll):
        """ Returns an approx guess without doing expensive calculations.
            This method should rely on other things later on.
            
            Should only be called during ongoing or closed polls.
        """
        response = {'added': len(poll), 'total': 0}
        wf_state = poll.get_workflow_state()
        if wf_state == 'ongoing':
            response['total'] = len(poll.voters_mark_ongoing)
        elif wf_state == 'closed':
            response['total'] = len(poll.voters_mark_closed)
        if response['total'] != 0:
            try:
                response['percentage'] = int(round(100 * Decimal(response['added']) / Decimal(response['total']), 0))
            except ZeroDivisionError:
                response['percentage'] = 0
        else:
            response['percentage'] = 0
        return response


class StrippedInlineAddForm(DefaultAddForm):
    title = None
    response_template = ""
    update_selector = ""

    @property
    def reply_to(self):
        """ If this form is in reply to something. """
        return self.request.GET.get('reply-to', False)

    def before(self, form):
        super(StrippedInlineAddForm, self).before(form)
        form.widget.template = 'voteit_form_inline'
        form.use_ajax = True

    def _response(self, *args, **kw):
        return Response(self.render_template(self.response_template, **kw))

    def save_success(self, appstruct):
        factory = self.get_content_factory(self.type_name)
        obj = factory(**appstruct)
        name = generate_slug(self.context, obj.uid)
        self.context[name] = obj
        return self._response(update_selector = self.update_selector)

    def cancel(self, *args):
        remove_parent = ''
        if self.reply_to:
            remove_parent = '[data-reply]'
        return self._response(remove_parent = remove_parent)

    cancel_success = cancel_failure = cancel


class ProposalAddForm(StrippedInlineAddForm):
    response_template = 'voteit.core:templates/portlets/inline_add_button_prop.pt'
    formid = 'proposal_inline_add'
    update_selector = '#ai-proposals'


class DiscussionAddForm(StrippedInlineAddForm):
    response_template = 'voteit.core:templates/portlets/inline_add_button_disc.pt'
    formid = 'discussion_inline_add'
    update_selector = '#ai-discussions'


def includeme(config):
    config.add_portlet_slot('agenda_item', title = _("Agenda Item portlets"), layout = 'vertical')
    config.add_portlet(ProposalsPortlet)
    config.add_portlet(DiscussionsPortlet)
    config.add_portlet(PollsPortlet)
    config.add_view(ProposalAddForm,
                    context = IAgendaItem,
                    name = 'add',
                    request_param = "content_type=Proposal",
                    permission = security.ADD_PROPOSAL,
                    renderer = 'arche:templates/form.pt')
    config.add_view(DiscussionAddForm,
                    context = IAgendaItem,
                    name = 'add',
                    request_param = "content_type=DiscussionPost",
                    permission = security.ADD_DISCUSSION_POST,
                    renderer = 'arche:templates/form.pt')
    config.add_view(ProposalsInline,
                    name = '__ai_proposals__',
                    context = IAgendaItem,
                    permission = security.VIEW,
                    renderer = 'voteit.core:templates/portlets/proposals_inline.pt')
    config.add_view(DiscussionsInline,
                    name = '__ai_discussions__',
                    context = IAgendaItem,
                    permission = security.VIEW,
                    renderer = 'voteit.core:templates/portlets/discussions_inline.pt')
    config.add_view(PollsInline,
                    name = '__ai_polls__',
                    context = IAgendaItem,
                    permission = security.VIEW,
                    renderer = 'voteit.core:templates/portlets/polls_inline.pt')
