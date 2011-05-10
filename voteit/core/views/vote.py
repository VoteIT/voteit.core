from pyramid.view import view_config
from pyramid.traversal import find_root, find_interface
from pyramid.url import resource_url
from pyramid.security import has_permission

import colander
from deform import Form
from deform.exception import ValidationFailure
from webob.exc import HTTPFound
from zope.component import getUtility

from voteit.core.views.api import APIView
from voteit.core.security import ROLE_OWNER, EDIT
from pyramid.exceptions import Forbidden
from voteit.core.models.interfaces import IVote
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin

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
        self.poll_plugin = getUtility(IPollPlugin, name = self.poll.poll_plugin_name)
        
        self.schema = self.poll_plugin.get_vote_schema(self.poll)


    @view_config(context=IPoll, name="vote", renderer=DEFAULT_TEMPLATE)
    def add_vote(self):
        """ Add a Vote to a Poll. """
        #Permission check
        #FIXME: Check if someone can vote
        #FIXME: Allow plugin to override renderer
        
        #Check if the users vote exists already
        userid = self.api.userid
        if userid in self.context:
            raise Forbidden("Already voted")

        self.form = Form(self.schema, buttons=('vote', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

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
            
            url = resource_url(vote, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response

    @view_config(context=IVote, name="edit", renderer=DEFAULT_TEMPLATE, permission=EDIT)
    def edit_vote(self):
        """ Edit vote, only for the owner of the vote. """
        #Permission check
        #FIXME: Check if someone can vote
        #FIXME: Allow plugin to override renderer
       
        self.form = Form(self.schema, buttons=('update', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'update' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = self.form.validate(controls)
                #FIXME: validate name - it must be unique and url-id-like
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            self.context.set_vote_data(appstruct)
            
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response

    @view_config(name="delete", renderer=DEFAULT_TEMPLATE)
    def delete_vote(self):
        #FIXME: Add permission checks
        #FIXME: Check workflow
        schema = colander.Schema()

        self.form = Form(schema, buttons=('delete', 'cancel'))
        self.response['form_resources'] = self.form.get_widget_resources()

        post = self.request.POST
        if 'delete' in post:
            parent = self.context.__parent__
            del parent[self.context.__name__]
            
            url = resource_url(parent, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = self.form.render()
        return self.response
