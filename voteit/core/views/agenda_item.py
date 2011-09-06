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



class AgendaItemView(BaseView):
    """ View for agenda items. """
    
    @view_config(context=IAgendaItem, renderer="templates/agenda_item.pt", permission=VIEW)
    def agenda_item_view(self):
        """ """

        self.response['get_discussions'] = self.get_discussions
        self.response['get_proposals'] = self.get_proposals
        self.response['polls'] = self.api.get_restricted_content(self.context, iface=IPoll, sort_on='created')
        
        ci = self.api.content_info
        url = resource_url(self.context, self.request)
        
        poll_forms = {}
        poll_form_resources = {}
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
                poll_forms[poll.uid] = form.render(appstruct=appstruct, readonly=True)
                poll_form_resources = form.get_widget_resources()

            else: 
                if has_permission(ADD_VOTE, poll, self.request):
                    poll_url = resource_url(poll, self.request)
                    form = Form(poll_schema, action=poll_url+"@@vote", buttons=(button_vote, button_cancel))
                    poll_forms[poll.uid] = form.render()
                    poll_form_resources = form.get_widget_resources()

        
        #Proposal form
        if has_permission(ci['Proposal'].add_permission, self.context, self.request):
            prop_schema = ci['Proposal'].schema(context=self.context, request=self.request, type='add')
            prop_form = Form(prop_schema, action=url+"@@add?content_type=Proposal", buttons=(button_add,))
        else:
            prop_form = Form(colander.Schema(), buttons=())

        #Discussion form
        if has_permission(ci['DiscussionPost'].add_permission, self.context, self.request):
            discussion_schema = ci['DiscussionPost'].schema(context=self.context, request=self.request, type='add')
            discussion_form = Form(discussion_schema, action=url+"@@add?content_type=DiscussionPost", buttons=(button_add,))
        else:
            discussion_form = Form(colander.Schema(), buttons=())

        #Join resources
        form_resources = prop_form.get_widget_resources()
        for (k, v) in discussion_form.get_widget_resources().items():
            if k in form_resources:
                form_resources[k].extend(v)
            else:
                form_resources[k] = v
        for (k, v) in poll_form_resources.items():
            if k in form_resources:
                form_resources[k].extend(v)
            else:
                form_resources[k] = v
        
        self.response['form_resources'] = form_resources
        self.response['poll_forms'] = poll_forms
        self.response['proposal_form'] = prop_form.render()
        self.response['discussion_form'] = discussion_form.render()

        return self.response

    def get_proposals(self):
        response = {}
        response['proposals'] = self.context.get_content(iface=IProposal, sort_on='created')
        response['like'] = _(u"Like")
        response['like_this'] = _(u"like this")
        response['api'] = self.api
        
        return render('templates/proposals.pt', response, request=self.request)
        
    def get_discussions(self):
        """ Get discussions for a specific context """
        
        limit = 5
        if 'discussions' in self.request.GET and self.request.GET['discussions'] == 'all':
            limit = 0
        
        discussions = self.context.get_content(iface=IDiscussionPost, sort_on='created')
        
        response = {}
        response['discussions'] = discussions[-limit:]
        if limit and limit < len(discussions):
            response['over_limit'] = len(discussions) - limit
        else:
            response['over_limit'] = 0
        
        response['like'] = _(u"Like")
        response['like_this'] = _(u"like this")
        response['api'] = self.api
        
        return render('templates/discussions.pt', response, request=self.request)
        
    @view_config(context=IAgendaItem, name="discussions", permission=VIEW, renderer='templates/discussions.pt')
    def meeting_messages(self):
        self.response['discussions'] = self.context.get_content(iface=IDiscussionPost, sort_on='created')
        return self.response
