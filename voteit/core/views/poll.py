from deform import Form
from deform.exception import ValidationFailure
from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.security import has_permission
from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.traversal import find_interface
from betahaus.pyracont.factories import createSchema
from pyramid.response import Response

from voteit.core.views.api import APIView
from voteit.core import VoteITMF as _
from voteit.core.security import ADD_VOTE
from voteit.core.security import EDIT
from voteit.core.security import VIEW
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IVote
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_vote
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_update
from voteit.core.models.schemas import button_save
from voteit.core.views.base_edit import BaseEdit
from voteit.core.schemas.poll import poll_schema_after_bind


class PollView(BaseEdit):
    """ View class for poll objects """
        
    @view_config(context=IPoll, name="edit", renderer='templates/base_edit.pt', permission=EDIT)
    def edit_form(self):
        content_type = self.context.content_type
        schema_name = self.api.get_schema_name(content_type, 'edit')
        schema = createSchema(schema_name, after_bind=poll_schema_after_bind).bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)

        form = Form(schema, buttons=(button_update, button_cancel))
        self.api.register_form_resources(form)

        post = self.request.POST
        if 'update' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response

            updated = self.context.set_field_appstruct(appstruct)
            if updated:
                self.api.flash_messages.add(_(u"Successfully updated"))
            else:
                self.api.flash_messages.add(_(u"Nothing updated"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        msg = _(u"Edit")
        self.api.flash_messages.add(msg, close_button=False)
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = form.render(appstruct=appstruct)
        return self.response

    @view_config(context=IPoll, name="poll_config", renderer='templates/base_edit.pt', permission=EDIT)
    def poll_config(self):
        """ Configure poll settings. Only for moderators.
            The settings themselves come from the poll plugin.
            Note that the Edit permission should only be granted to moderators
            before the actual poll has been set in the ongoing state. After that,
            no settings may be changed.
        """
        self.response['title'] = _(u"Poll config")

        poll_plugin = self.context.get_poll_plugin()
        schema = poll_plugin.get_settings_schema()
        if schema is None:
            raise Forbidden("No settings for this poll")
        add_csrf_token(self.context, self.request, schema)

        form = Form(schema, buttons=(button_save, button_cancel))
        self.api.register_form_resources(form)

        #FIXME: Better default text
        config_back_msg = _(u"review_poll_settings_info_getback",
                default = u"To get back to the poll settings you click the cogwheel menu and select configure poll.")

        post = self.request.POST
        if 'save' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            del appstruct['csrf_token'] #Otherwise it will be stored too
            self.context.poll_settings = appstruct
            
            self.api.flash_messages.add(config_back_msg)
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(config_back_msg)
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        self.response['form'] = form.render(appstruct=self.context.poll_settings)
        return self.response
        
    @view_config(context=IPoll, renderer="templates/polls.pt")
    def poll_view(self):
        """ Poll view should redirect to parent agenda item it the request is not a xhr request
        """
        if not self.request.is_xhr:
            url = resource_url(self.context.__parent__, self.request)
            return HTTPFound(location=url)
        
        self.response['polls'] = (self.context, )
        poll_forms = {}
        for poll in self.response['polls']:
            #Check if the users vote exists already
            userid = self.api.userid
            try:
                plugin = poll.get_poll_plugin()
            except ComponentLookupError:
                err_msg = _(u"plugin_missing_error",
                            default = u"Can't find any poll plugin with name '${name}'. Perhaps that package has been uninstalled?",
                            mapping = {'name': poll.get_field_value('poll_plugin')})
                self.api.flash_messages.add(err_msg, type="error")
                poll_forms[poll.uid] = ''
                continue
            poll_schema = plugin.get_vote_schema()
            appstruct = {}
            can_vote = has_permission(ADD_VOTE, poll, self.request)

            if can_vote:
                poll_url = resource_url(poll, self.request)
                form = Form(poll_schema, action=poll_url+"@@vote", buttons=(button_vote,), formid=poll.__name__, use_ajax=True)
            else:
                form = Form(poll_schema, formid=poll.__name__, use_ajax=True)
            self.api.register_form_resources(form)

            if userid in poll:
                #If editing a vote is allowed, redirect. Editing is only allowed in open polls
                vote = poll.get(userid)
                assert IVote.providedBy(vote)
                #show the users vote and edit button
                appstruct = vote.get_vote_data()
                #Poll might still be open, in that case the poll should be changable
                readonly = not can_vote
                poll_forms[poll.uid] = form.render(appstruct=appstruct, readonly=readonly)
            #User has not voted
            elif can_vote:
                poll_forms[poll.uid] = form.render()
        self.response['poll_forms'] = poll_forms
        
        return self.response
    
    @view_config(context=IPoll, name="poll_raw_data", permission=VIEW)
    def poll_raw_data(self):
        """ View for all ballots. See intefaces.IPollPlugin.render_raw_data
        """
        #Poll closed?
        if self.context.get_workflow_state() != 'closed':
            self.api.flash_messages.add("Poll not closed yet", type='error')
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #This will generate a ComponentLookupError if the plugin isn't found,
        #however, that should never happen for a closed poll unless someone
        #removed the plugin.
        plugin = self.context.get_poll_plugin()
        return plugin.render_raw_data()

    @view_config(context=IPoll, name="vote", permission=ADD_VOTE, renderer='templates/ajax_edit.pt')
    def vote_action(self):
        """ Adds or updates a users vote. """
        ai = find_interface(self.context, IAgendaItem)
        ai_url = resource_url(ai, self.request)
        url = resource_url(self.context, self.request)
        
        post = self.request.POST
        if 'vote' not in post:
            return HTTPForbidden()
        
        options = """
        {success:
          function (rText, sText, xhr, form) {
            var url = xhr.getResponseHeader('X-Relocate');
            if (url) {
              document.location = url;
            };
           }
        }
        """

        poll_plugin = self.context.get_poll_plugin()
        schema = poll_plugin.get_vote_schema()
        add_csrf_token(self.context, self.request, schema)
        form = Form(schema, 
                    action=url+"@@vote", 
                    buttons=(button_vote,), 
                    formid=self.context.__name__, 
                    use_ajax=True,
                    ajax_options=options)
        self.api.register_form_resources(form)

        userid = self.api.userid
        controls = post.items()
        try:
            #appstruct is deforms convention. It will be the submitted data in a dict.
            appstruct = form.validate(controls)
        except ValidationFailure, e:
            #FIXME: How do we validate this properly, and display the result?
            self.response['form'] = e.render()
            return self.response
            
        Vote = poll_plugin.get_vote_class()
        if not IVote.implementedBy(Vote):
            raise TypeError("Poll plugins method get_vote_class returned something that didn't implement IVote.")

        #Remove crsf_token from appstruct after validation
        del appstruct['csrf_token']

        if userid in self.context:
            vote = self.context[userid]
            assert IVote.providedBy(vote)
            vote.set_vote_data(appstruct)
            msg = _(u"Your vote was updated.")
        else:
            vote = Vote(creators = [userid])
            #We don't need to send events here, since object added will take care of that
            vote.set_vote_data(appstruct, notify = False)
            #To fire events after set_vote_data is done
            self.context[userid] = vote
            msg = _(u"Thank you for voting!")
        self.api.flash_messages.add(msg)
        
        return Response(headers = [('X-Relocate', ai_url)])