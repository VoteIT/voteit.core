""" Portlets that by default will be rendered within the Agenda Item view.
    They can be rearranged or disabled by changing them within the meeting context.
"""
from __future__ import unicode_literals

from arche.portlets import PortletType
from arche.utils import generate_slug
from arche.views.base import BaseView
from arche.views.base import DefaultAddForm
from deform_autoneed import need_lib
from pyramid.renderers import render
from pyramid.response import Response
#from pyramid.traversal import find_interface
#from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from repoze.catalog.query import Eq, NotAny, Any
#import colander

from voteit.core import _
from voteit.core import security
from voteit.core.fanstaticlib import data_loader
from voteit.core.models.interfaces import IAgendaItem
#from voteit.core.models.interfaces import IProposal
#from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.schemas.meeting import AgendaItemProposalsPortletSchema

#FIXME: Loading required resources for inline forms is still a problem.

class ListingPortlet(PortletType):
    schema_factory = None

    def render(self, context, request, view, **kwargs):
        if IAgendaItem.providedBy(context):
            data_loader.need()
            need_lib('deform')
            query = {}
            tag = request.GET.get('tag', None)
            if tag:
                query['tag'] = tag
            hide = []
            if self.portlet.settings.get('hide_retracted', False):
                hide.append('retracted')
            if self.portlet.settings.get('hide_unhandled_proposals', False):
                hide.append('unhandled')
            query['hide'] = hide
            url = request.resource_url(context, self.view_name, query = query)
            response = {'portlet': self.portlet, 'view': view, 'load_url': url}
            return render(self.template, response, request = request)


class ProposalsPortlet(ListingPortlet):
    name = "ai_proposals"
    title = _("Agenda Item: Proposals listing")
    template = "voteit.core:templates/portlets/proposals.pt"
    view_name = '__ai_proposals__'
    schema_factory = AgendaItemProposalsPortletSchema


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
#    schema_factory = FIXME: Schema for listing


class ProposalsInline(BaseView):
    
    def __call__(self):
        query = Eq('path', resource_path(self.context)) &\
                Eq('type_name', 'Proposal')
        hide = self.request.GET.getall('hide')
        if hide:
            query &= NotAny('workflow_state', hide)
        tag = self.request.GET.get('tag', None)
        if tag:
            #Only apply tag limit for things that aren't polls.
            #This is a safegard against user errors
            query &= Any('tags', (tag, ))
        response = {}
        response['contents'] = self.catalog_query(query, resolve = True, sort_index = 'created')
        return response


class DiscussionsInline(BaseView):
    
    def __call__(self):
        query = {
            'path': resource_path(self.context),
            'type_name': 'DiscussionPost',
            'sort_index': 'created'}
        tag = self.request.GET.get('tag', None)
        if tag:
            query['tags'] = tag
        response = {}
        response['contents'] = self.catalog_search(resolve = True, **query)
        return response


class PollsInline(BaseView):
    
    def __call__(self):
        query = {
            'path': resource_path(self.context),
            'type_name': 'Poll',
            'sort_index': 'created',}
        response = {}
        response['contents'] = self.catalog_search(resolve = True, **query)
        response['vote_perm'] = security.ADD_VOTE
        return response


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
        return self._response(update_selector = self.update_selector)

    cancel_success = cancel_failure = _response


class ProposalAddForm(StrippedInlineAddForm):
    response_template = 'voteit.core:templates/portlets/inline_dummy_proposal_button.pt'
    formid = 'proposal_inline_add'
    update_selector = '#ai-proposals'


class DiscussionAddForm(StrippedInlineAddForm):
    response_template = 'voteit.core:templates/portlets/inline_dummy_form.pt'
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
                    permission = security.ADD_AGENDA_ITEM,
                    renderer = 'arche:templates/form.pt')
    config.add_view(DiscussionAddForm,
                    context = IAgendaItem,
                    name = 'add',
                    request_param = "content_type=DiscussionPost",
                    permission = security.ADD_AGENDA_ITEM,
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
