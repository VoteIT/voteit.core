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
from pyramid.traversal import find_interface
from pyramid.traversal import find_root
from pyramid.traversal import resource_path
from repoze.catalog.query import Eq, NotAny, Any
import colander

from voteit.core import _
from voteit.core import security
from voteit.core.fanstaticlib import data_loader
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.schemas.meeting import AgendaItemProposalsPortletSchema
#from fanstatic.core import get_needed

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
    template = "voteit.core:views/templates/portlets/proposals.pt"
    view_name = '__ai_proposals__'
    schema_factory = AgendaItemProposalsPortletSchema


class DiscussionsPortlet(ListingPortlet):
    name = "ai_discussions"
    title = _("Agenda Item: Discussions listing")
    template = "voteit.core:views/templates/portlets/discussions.pt"
    view_name = '__ai_discussions__'


# def inline_add_proposal_form(context, request, va, **kw):
#     """ For agenda item contexts.
#     """
#     api = kw['api']
#     #jquery_form.need() #This isn't included in widgets for some reason
#     form = inline_add_form(api, 'Proposal', {})
#     api.register_form_resources(form)
#     if not api.context_has_permission(ADD_PROPOSAL, context):
#         if context.get_workflow_state() == 'closed':
#             msg = api.translate(_(u"no_propose_ai_closed",
#                                   default = u"The agenda item is closed, you can't add a proposal here"))
#         elif api.meeting.get_workflow_state() == 'closed':
#             msg = api.translate(_(u"no_propose_meeting_closed",
#                                   default = u"The meeting is closed, you can't add a proposal here"))
#         else:
#             msg = api.translate(_(u"no_propose_perm_notice",
#                                   default = u"You don't have the required permission to add a proposal here"))
#         return "<hr/>%s" % msg
#     response = {}
#     query = {'content_type': 'Proposal'}
#     tag = request.GET.get('tag', None)
#     if tag:
#         query['tag'] = tag
#     response['url'] = request.resource_url(context, '_inline_form', query = query)
#     response['text'] = _(u'${username} propose', mapping={'username': api.userid})
#     return render('../templates/snippets/inline_dummy_proposal_button.pt', response, request = request)



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
            #query['tags'] = tag
            
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
        response['contents'] = self.catalog_query(query, resolve = True, sort_index = 'created')
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


class DiscussionsInline(BaseView):
    
    def __call__(self):
        query = {
            'path': resource_path(self.context),
            'type_name': 'DiscussionPost',
            'sort_index': 'created',
             }
        tag = self.request.GET.get('tag', None)
        if tag:
            query['tags'] = tag
        response = {}
        response['contents'] = self.catalog_search(resolve = True, **query)
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
    response_template = 'voteit.core:views/templates/portlets/inline_dummy_proposal_button.pt'
    formid = 'proposal_inline_add'
    update_selector = '#ai-proposals'


class DiscussionAddForm(StrippedInlineAddForm):
    response_template = 'voteit.core:views/templates/portlets/inline_dummy_form.pt'
    formid = 'discussion_inline_add'
    update_selector = '#ai-discussions'


def includeme(config):
    config.add_portlet_slot('agenda_item', title = _("Agenda Item portlets"), layout = 'vertical')
    config.add_portlet(ProposalsPortlet)
    config.add_portlet(DiscussionsPortlet)
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
                    renderer = 'voteit.core:views/templates/portlets/proposals_inline.pt')
    config.add_view(DiscussionsInline,
                    name = '__ai_discussions__',
                    context = IAgendaItem,
                    permission = security.VIEW,
                    renderer = 'voteit.core:views/templates/portlets/discussions_inline.pt')
