from pyramid.renderers import get_renderer, render
from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.security import has_permission
from webob.exc import HTTPFound
from deform import Form
import colander

from voteit.core import VoteITMF as _
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IDiscussionPost
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IProposal
from voteit.core.models.interfaces import IVote
from voteit.core.security import VIEW, EDIT, ADD_VOTE
from voteit.core.models.schemas import button_add, button_cancel, button_vote
from pyramid.traversal import resource_path



class AgendaItemView(BaseView):
    """ View for agenda items. """
    
    @view_config(context=IAgendaItem, renderer="templates/agenda_item.pt", permission=VIEW)
    def agenda_item_view(self):
        """ """

        self.response['get_discussions'] = self.get_discussions
        self.response['get_proposals'] = self.get_proposals
        self.response['get_polls'] = self.get_polls
        self.response['polls'] = self.api.get_restricted_content(self.context, iface=IPoll, sort_on='created')
        
        ci = self.api.content_info
        url = resource_url(self.context, self.request)
        
        poll_forms = {}
        for poll in self.response['polls']:
            #Check if the users vote exists already
            userid = self.api.userid
            poll_schema = poll.get_poll_plugin().get_vote_schema()
            appstruct = {}
            if userid in poll:
                #If editing a vote is allowed, redirect. Editing is only allowed in open polls
                vote = poll.get(userid)
                assert IVote.providedBy(vote)
                
                #show the users vote and edit button
                appstruct = vote.get_vote_data()
                
                form = Form(poll_schema)
                self.api.register_form_resources(form)
                poll_forms[poll.uid] = form.render(appstruct=appstruct, readonly=True)

            else: 
                if has_permission(ADD_VOTE, poll, self.request):
                    poll_url = resource_url(poll, self.request)
                    form = Form(poll_schema, action=poll_url+"@@vote", buttons=(button_vote, button_cancel))
                    self.api.register_form_resources(form)
                    poll_forms[poll.uid] = form.render()

        
        #Proposal form
        if has_permission(ci['Proposal'].add_permission, self.context, self.request):
            prop_schema = ci['Proposal'].schema(context=self.context, request=self.request, type='add')
            prop_form = Form(prop_schema, action=url+"@@add?content_type=Proposal", buttons=(button_add,))
            self.api.register_form_resources(prop_form)
        else:
            prop_form = None

        #Discussion form
        if has_permission(ci['DiscussionPost'].add_permission, self.context, self.request):
            discussion_schema = ci['DiscussionPost'].schema(context=self.context, request=self.request, type='add')
            discussion_form = Form(discussion_schema, action=url+"@@add?content_type=DiscussionPost", buttons=(button_add,))
            self.api.register_form_resources(discussion_form)
        else:
            discussion_form = None

        self.response['poll_forms'] = poll_forms
        self.response['proposal_form'] = prop_form and prop_form.render()
        self.response['discussion_form'] = discussion_form and discussion_form.render()

        return self.response
        
    def _show_retract(self, context):
        return context.content_type == 'Proposal' and \
            self.api.context_has_permission('Retract', context) and \
            context.get_workflow_state() == 'published'

    def get_polls(self, polls, poll_forms):
        response = {}
        response['api'] = self.api
        response['polls'] = polls
        response['poll_forms'] = poll_forms
        return render('templates/polls.pt', response, request=self.request)

    def get_proposals(self):
        response = {}
        response['proposals'] = self.context.get_content(iface=IProposal, sort_on='created')
        response['like'] = _(u"Like")
        response['like_this'] = _(u"like this")
        response['api'] = self.api
        response['show_retract'] = self._show_retract
        
        return render('templates/proposals.pt', response, request=self.request)
        
    def get_discussions(self):
        """ Get discussions for a specific context """
        
        limit = 5
        if self.request.GET.get('discussions', '') == 'all':
            limit = 0
        
        path = resource_path(self.context)
        #Returns tuple of (item_count, list of docids)
        count, docids = self.api.search_catalog(path=path, content_type='DiscussionPost', sort_index='created')
        docids = tuple(docids) #Convert, since it's a generator
        
        #Only fetch metadata that is within limit
        discussions = [self.api.resolve_catalog_docid(x) for x in docids[-limit:]]

        response = {}
        response['discussions'] = tuple(discussions)
        if limit and limit < count:
            response['over_limit'] = count - limit
        else:
            response['over_limit'] = 0
            
        response['limit'] = limit
        
        response['like'] = _(u"Like")
        response['like_this'] = _(u"like this")
        response['api'] = self.api
        
        return render('templates/discussions.pt', response, request=self.request)

    @view_config(context=IAgendaItem, name="discussions", permission=VIEW, renderer='templates/discussions.pt')
    def meeting_messages(self):
        self.response['discussions'] = self.context.get_content(iface=IDiscussionPost, sort_on='created')
        return self.response
