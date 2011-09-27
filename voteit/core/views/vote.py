from pyramid.exceptions import Forbidden
from pyramid.view import view_config
from pyramid.traversal import find_root, find_interface
from pyramid.url import resource_url
from pyramid.security import has_permission
import colander
from deform import Form
from deform.exception import ValidationFailure
from webob.exc import HTTPFound

from voteit.core import VoteITMF as _
from voteit.core.views.api import APIView
from voteit.core.security import ROLE_OWNER, EDIT, DELETE, ADD_VOTE, VIEW
from voteit.core.models.interfaces import IVote
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.schemas import add_csrf_token, button_vote,\
    button_cancel, button_update, button_delete

DEFAULT_TEMPLATE = "templates/base_edit.pt"


class VoteView(object):
    """ View class for adding, editing or deleting votes. """
        
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.response = {}
        self.response['api'] = self.api = APIView(context, request)

        if not self.api.userid:
            raise Forbidden("No UserID found.")
        
        self.poll = find_interface(context, IPoll)
        self.poll_plugin = self.poll.get_poll_plugin()
        
        self.schema = self.poll_plugin.get_vote_schema()


    @view_config(context=IPoll, name="vote", renderer=DEFAULT_TEMPLATE, permission=ADD_VOTE)
    def add_vote(self):
        """ Add a Vote to a Poll. """
        #FIXME: Allow plugin to override renderer
        
        #Check if the users vote exists already
        userid = self.api.userid
        if userid in self.context:
            #If editing a vote is allowed, redirect. Editing is only allowed in open polls
            vote = self.context.get(userid)
            assert IVote.providedBy(vote)
            
            if has_permission(EDIT, vote, self.request):
                msg = _('already_voted_poll_open', default=u"You've already voted, but the poll is still open so you can change your vote if you want to.")
                self.api.flash_messages.add(msg)
                url = "%sedit" % resource_url(vote, self.request)
                return HTTPFound(location=url)
            
            raise Forbidden("You've already voted and the poll is closed.")

        self.form = Form(self.schema, buttons=(button_vote, button_cancel))
        self.api.register_form_resources(self.form)

        post = self.request.POST
        if 'vote' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = self.form.validate(controls)
                #FIXME: validate name - it must be unique and url-id-like
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            Vote = self.poll_plugin.get_vote_class()
            if not IVote.implementedBy(Vote):
                raise TypeError("Poll plugins method get_vote_class returned something that didn't implement IVote.")
            vote = Vote()
            vote.creators = [userid]
            vote.add_groups(userid, (ROLE_OWNER,))
            vote.set_vote_data(appstruct)
            
            self.context[userid] = vote
            
            msg = _(u"Thank you for voting!")
            self.api.flash_messages.add(msg)
            ai = find_interface(vote, IAgendaItem)
            url = resource_url(ai, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            msg = _(u"Canceled - your vote has NOT been added!")
            self.api.flash_messages.add(msg)
            ai = find_interface(self.context, IAgendaItem)
            url = resource_url(ai, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        msg = _(u"Add a vote")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = self.form.render()
        return self.response

    @view_config(context=IVote, name="edit", renderer=DEFAULT_TEMPLATE, permission=EDIT)
    def edit_vote(self):
        """ Edit vote, only for the owner of the vote. """
        #FIXME: Allow plugin to override renderer?
       
        self.form = Form(self.schema, buttons=(button_update, button_cancel))
        self.api.register_form_resources(self.form)

        post = self.request.POST
        if 'update' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = self.form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            self.context.set_vote_data(appstruct)

            msg = _(u"Your vote has been updated.")
            self.api.flash_messages.add(msg)

            ai = find_interface(self.context, IAgendaItem)
            url = resource_url(ai, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            msg = _(u"Canceled - vote NOT updated!")
            self.api.flash_messages.add(msg)
            ai = find_interface(self.context, IAgendaItem)
            url = resource_url(ai, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        msg = _(u"Edit your vote")
        self.api.flash_messages.add(msg, close_button=False)
        appstruct = self.context.get_vote_data()
        self.response['form'] = self.form.render(appstruct=appstruct)
        return self.response
        
    @view_config(context=IVote, name="delete", permission=DELETE, renderer=DEFAULT_TEMPLATE)
    def delete_form(self):

        schema = colander.Schema()
        add_csrf_token(self.context, self.request, schema)
        
        self.form = Form(schema, buttons=(button_delete, button_cancel))
        self.api.register_form_resources(self.form)

        post = self.request.POST
        if 'delete' in post:

            parent = self.context.__parent__
            del parent[self.context.__name__]

            self.api.flash_messages.add(_(u"Deleted"))

            ai = find_interface(parent, IAgendaItem)
            url = resource_url(ai, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            ai = find_interface(self.context, IAgendaItem)
            url = resource_url(ai, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        msg = _(u"Are you sure you want to delete this item?")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = self.form.render()
        return self.response

    @view_config(context=IVote, renderer='templates/base_readonly_form.pt', permission=VIEW)
    def view_vote(self):

        self.form = Form(self.schema, buttons=())
        self.api.register_form_resources(self.form)

        msg = _(u"This is your vote")
        self.api.flash_messages.add(msg, close_button=False)

        appstruct = self.context.get_vote_data()
        self.response['readonly_form'] = self.form.render(appstruct=appstruct, readonly=True)
        return self.response
