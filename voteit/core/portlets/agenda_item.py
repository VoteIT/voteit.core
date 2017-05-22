""" Portlets that by default will be rendered within the Agenda Item view.
    They can be rearranged or disabled by changing them within the meeting context.
"""
from __future__ import unicode_literals

from copy import copy
from decimal import Decimal

from arche.portlets import PortletType
from arche.utils import generate_slug
from arche.views.base import BaseView
from arche.views.base import DefaultAddForm
from pyramid.httpexceptions import HTTPForbidden
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.traversal import resource_path
from repoze.catalog.query import Eq, NotAny, Any
from repoze.workflow import WorkflowError
from voteit.core import _
from voteit.core import security
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IProposal
from voteit.core.security import ADD_POLL
from voteit.core.views.base_inline import ProposalInlineMixin
from voteit.core.views.base_inline import PollInlineMixin


# FIXME: Loading required resources for inline forms is still a problem.
# Fanstatic must fetch required resources on the base view


class ListingPortlet(PortletType):
    schema_factory = None

    def render(self, context, request, view, **kwargs):
        if IAgendaItem.providedBy(context):
            query = {}
            tags = request.GET.getall('tag')
            if tags:
                query['tag'] = [x.lower() for x in tags]
            url = request.resource_url(context, self.view_name, query=query)
            response = {'portlet': self.portlet, 'view': view, 'load_url': url}
            return render(self.template, response, request=request)


class ProposalsPortlet(ListingPortlet):
    name = "ai_proposals"
    title = _("Proposals")
    template = "voteit.core:templates/portlets/proposals.pt"
    view_name = '__ai_proposals__'

    def render(self, context, request, view, **kwargs):
        if IAgendaItem.providedBy(context):
            query = {}
            tags = request.GET.getall('tag')
            if tags:
                query['tag'] = [x.lower() for x in tags]
            query['hide'] = tuple(request.meeting.hide_proposal_states)
            url = request.resource_url(context, self.view_name, query=query)
            response = {'portlet': self.portlet, 'view': view, 'load_url': url}
            return render(self.template, response, request=request)


class DiscussionsPortlet(ListingPortlet):
    name = "ai_discussions"
    title = _("Discussion")
    template = "voteit.core:templates/portlets/discussions.pt"
    view_name = '__ai_discussions__'


class PollsPortlet(ListingPortlet):
    name = "ai_polls"
    title = _("Polls")
    template = "voteit.core:templates/portlets/polls.pt"
    view_name = '__ai_polls__'

    def render(self, context, request, view, **kwargs):
        if IAgendaItem.providedBy(context):
            query = "type_name == 'Poll' and path == '%s'" % resource_path(context)
            query += " and workflow_state in any(['ongoing', 'upcoming', 'closed'])"
            if request.is_moderator or view.catalog_query(query):
                url = request.resource_url(context, self.view_name)
                response = {'portlet': self.portlet, 'view': view, 'load_url': url}
                return render(self.template, response, request=request)


class ProposalsInline(BaseView):
    def __call__(self):
        response = {}
        query = Eq('path', resource_path(self.context)) & \
                Eq('type_name', 'Proposal')
        tags = self.request.GET.getall('tag')
        if tags:
            tags = [x.lower() for x in tags]
            query &= Any('tags', tags)
        hide = self.request.params.getall('hide')
        load_hidden = self.request.params.get('load_hidden', False)
        if load_hidden:
            # Only load data previously hidden
            if hide:
                query &= Any('workflow_state', hide)
        else:
            invert_hidden = copy(query)
            # Normal operation, keep count of hidden
            if hide:
                invert_hidden &= Any('workflow_state', hide)
                query &= NotAny('workflow_state', hide)
        response['docids'] = tuple(self.catalog_query(query, sort_index='created'))
        read_names = self.request.get_read_names(self.context)
        unread_query = query & NotAny('__name__',
                                      set(read_names.get(self.request.authenticated_userid, [])))
        response['unread_docids'] = tuple(self.catalog_query(unread_query,
                                                             sort_index='created'))
        response['contents'] = self.resolve_docids(response['docids'])  # A generator
        if not load_hidden:
            response['hidden_count'] = self.request.root.catalog.query(invert_hidden)[0].total
            get_query = {'tag': tags, 'load_hidden': 1, 'hide': hide}
            response['load_hidden_url'] = self.request.resource_url(self.context,
                                                                    self.request.view_name,
                                                                    query=get_query)
        else:
            response['hidden_count'] = False
        return response


class ProposalsInlineStateChange(BaseView, ProposalInlineMixin):

    def __call__(self):
        new_state = self.request.GET.get('state')
        # change state
        try:
            self.context.set_workflow_state(self.request, new_state)
        except WorkflowError as exc:
            raise HTTPForbidden(str(exc))
        return self.get_context_response()


class DiscussionsInline(BaseView):

    def __call__(self):
        """ Loading procedure of discussion posts:
            If nothing specific is set, limit loading to the next 5 unread.
            If there aren't 5 unread, fetch the 5 last posts.
            If there are more unread than 5, create a link to load more.
        """
        query = {}
        query['tags'] = [x.lower() for x in self.request.GET.getall('tag')]
        query['limit'] = 5
        if self.request.GET.get('previous', False):
            query['limit'] = 0
            query['end_before'] = int(self.request.GET.get('end_before'))
        if self.request.GET.get('next', False):
            query['start_after'] = int(self.request.GET.get('start_after'))
        response = self.request.get_docids_to_show(self.context, 'DiscussionPost', **query)
        response['contents'] = self.resolve_docids(response['batch'])  # Generator
        if response['previous'] and response['batch']:
            end_before = response['batch'][0]
            response['load_previous_url'] = self.request.resource_url(
                self.context, '__ai_discussions__',
                query={'tag': query['tags'],
                       'previous': 1,
                       'end_before': end_before}
            )
        if response['over_limit'] and response['batch']:
            start_after = response['batch'][-1]
            response['load_next_url'] = self.request.resource_url(
                self.context, '__ai_discussions__',
                query={'tag': query['tags'],
                       'next': 1,
                       'start_after': start_after}
            )
        return response


class PollsInline(BaseView):
    def __call__(self):
        query = {
            'path': resource_path(self.context),
            'type_name': 'Poll',
            'sort_index': 'created', }
        response = {}
        response['contents'] = tuple(self.catalog_search(resolve=True, **query))
        response['vote_perm'] = security.ADD_VOTE
        response['show_add'] = self.request.is_moderator and self.request.has_permission(ADD_POLL,
                                                                                         self.context)
        return response

    def get_poll_filter_url(self, poll):
        tags = set()
        for prop in poll.get_proposal_objects():
            tags.add(prop.aid)
        return self.request.resource_url(poll.__parent__, query={'tag': tags})

    def get_voted_estimate(self, poll):
        """ Returns an approx guess without doing expensive calculations.
            This method should rely on other things later on.
            
            Should only be called during ongoing or closed polls.
        """
        response = {'added': len(poll), 'total': 0}
        wf_state = poll.get_workflow_state()
        if wf_state == 'ongoing':
            response['total'] = len(
                tuple(self.request.meeting.local_roles.get_any_local_with(security.ROLE_VOTER)))
        elif wf_state == 'closed':
            response['total'] = len(poll.voters_mark_closed)
        if response['total'] != 0:
            try:
                response['percentage'] = int(
                    round(100 * Decimal(response['added']) / Decimal(response['total']), 0))
            except ZeroDivisionError:
                response['percentage'] = 0
        else:
            response['percentage'] = 0
        return response


class PollsInlineStateChange(PollsInline, PollInlineMixin):
    def __call__(self):
        new_state = self.request.GET.get('state')
        # change state
        try:
            self.context.set_workflow_state(self.request, new_state)
        except WorkflowError as exc:
            raise HTTPForbidden(str(exc))
        return self.get_context_response()


class StrippedInlineAddForm(DefaultAddForm):
    title = None
    response_template = ""
    update_selector = ""

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
        return self._response(update_selector=self.update_selector)

    def cancel(self, *args):
        return self._response()

    cancel_success = cancel_failure = cancel


class ProposalAddForm(StrippedInlineAddForm):
    response_template = 'voteit.core:templates/portlets/inline_add_button_prop.pt'
    formid = 'proposal_inline_add'
    update_selector = '#ai-proposals'


class DiscussionAddForm(StrippedInlineAddForm):
    response_template = 'voteit.core:templates/portlets/inline_add_button_disc.pt'
    update_structure_tpl = 'voteit.core:templates/snippets/js_update_structure.pt'
    update_selector = '#ai-discussions'

    @property
    def formid(self):
        if self.reply_to:
            return "discussion_add_reply_to_%s" % self.reply_to
        return "discussion_inline_add"

    @property
    def reply_to(self):
        return self.request.GET.get('reply-to')

    @property
    def form_options(self):
        options = dict(super(DiscussionAddForm, self).form_options)
        if self.reply_to:
            options.update({'css_class': 'deform discussion-reply-to'})
        return options

    def save_success(self, appstruct):
        factory = self.get_content_factory(self.type_name)
        obj = factory(**appstruct)
        name = generate_slug(self.context, obj.uid)
        self.context[name] = obj
        if not self.reply_to:
            return self._response(update_selector=self.update_selector)
        return Response(self.render_template(self.update_structure_tpl,
                                             hide_popover='[data-reply-to="%s"]' % self.reply_to,
                                             scroll_to='#ai-discussions .list-group-item:last',
                                             load_target="%s [data-load-target]" % self.update_selector))

    def cancel(self, *args):
        if not self.reply_to:
            return self._response()
        return Response(self.render_template(self.update_structure_tpl,
                                             hide_popover='[data-reply-to="%s"]' % self.reply_to))

    cancel_success = cancel_failure = cancel


def includeme(config):
    config.add_portlet_slot('agenda_item', title=_("Agenda Item portlets"), layout='vertical')
    config.add_portlet(ProposalsPortlet)
    config.add_portlet(DiscussionsPortlet)
    config.add_portlet(PollsPortlet)
    config.add_view(ProposalAddForm,
                    context=IAgendaItem,
                    name='add',
                    request_param="content_type=Proposal",
                    permission=security.ADD_PROPOSAL,
                    renderer='arche:templates/form.pt')
    config.add_view(DiscussionAddForm,
                    context=IAgendaItem,
                    name='add',
                    request_param="content_type=DiscussionPost",
                    permission=security.ADD_DISCUSSION_POST,
                    renderer='arche:templates/form.pt')
    config.add_view(ProposalsInline,
                    name='__ai_proposals__',
                    context=IAgendaItem,
                    permission=security.VIEW,
                    renderer='voteit.core:templates/portlets/proposals_inline.pt')
    config.add_view(ProposalsInlineStateChange,
                    name='__inline_state_change__',
                    context=IProposal,
                    permission=security.VIEW,
                    renderer='voteit.core:templates/portlets/proposals_inline.pt')
    config.add_view(DiscussionsInline,
                    name='__ai_discussions__',
                    context=IAgendaItem,
                    permission=security.VIEW,
                    renderer='voteit.core:templates/portlets/discussions_inline.pt')
    config.add_view(PollsInline,
                    name='__ai_polls__',
                    context=IAgendaItem,
                    permission=security.VIEW,
                    renderer='voteit.core:templates/portlets/polls_inline.pt')
    config.add_view(PollsInlineStateChange,
                    name='__inline_state_change__',
                    context=IPoll,
                    permission=security.VIEW,
                    renderer='voteit.core:templates/portlets/polls_inline.pt')
