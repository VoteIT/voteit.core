from deform import Form
from deform.exception import ValidationFailure
from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.security import has_permission
from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from betahaus.pyracont.factories import createSchema
from pyramid.renderers import render
from pyramid.response import Response

from voteit.core import VoteITMF as _
from voteit.core import security
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
        
    @view_config(context=IPoll, name="edit", renderer='templates/base_edit.pt', permission = security.EDIT)
    def edit_form(self):
        """ For configuring polls that haven't started yet. """
        schema_name = self.api.get_schema_name(self.context.content_type, 'edit')
        schema = createSchema(schema_name, after_bind=poll_schema_after_bind)
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
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

            removed_uids = set(self.context.proposal_uids) - set(appstruct['proposals'])
            if removed_uids:
                #Adjust removed proposals back to published state, if they're locked
                for uid in removed_uids:
                    prop = self.context.get_proposal_by_uid(uid)
                    if prop.get_workflow_state() == 'voting':
                        prop.set_workflow_state(self.request, u'published')

            updated = self.context.set_field_appstruct(appstruct)
            if updated:
                self.api.flash_messages.add(_(u"Successfully updated"))
            else:
                self.api.flash_messages.add(_(u"Nothing changed"))

            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        appstruct = self.context.get_field_appstruct(schema)
        self.response['form'] = form.render(appstruct=appstruct)
        return self.response

    @view_config(context=IPoll, name="poll_config", renderer='templates/base_edit.pt', permission=security.EDIT)
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
        schema = schema.bind(context=self.context, request=self.request, api = self.api)

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

    @view_config(name="_poll_form", context=IPoll, renderer="templates/ajax_edit.pt", permission=security.VIEW, xhr=True)
    def poll_form(self):
        """ Return rendered poll form or process a vote. """
        poll_plugin = self.context.get_poll_plugin()
        schema = poll_plugin.get_vote_schema(self.request, self.api)
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)        
        form = Form(schema,
                    action=self.request.resource_url(self.context, '_poll_form'),
                    buttons=(button_vote,),
                    formid="vote_form")
        can_vote = has_permission(security.ADD_VOTE, self.context, self.request)
        userid = self.api.userid
        post = self.request.POST
        if 'vote' in post:
            if not can_vote:
                raise HTTPForbidden(u"You're not allowed to vote")
            controls = post.items()
            try:
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.request
            Vote = poll_plugin.get_vote_class()
            if not IVote.implementedBy(Vote):
                raise TypeError("Poll plugins method get_vote_class returned something that didn't implement IVote.")
            #Remove crsf_token from appstruct after validation
            del appstruct['csrf_token']
            if userid in self.context:
                vote = self.context[userid]
                assert IVote.providedBy(vote)
                vote.set_vote_data(appstruct)
                #FIXME: success_msg = _(u"Your vote was updated.")
            else:
                vote = Vote(creators = [userid])
                #We don't need to send events here, since object added will take care of that
                vote.set_vote_data(appstruct, notify = False)
                #To fire events after set_vote_data is done
                self.context[userid] = vote
                #FIXME: success_msg = _(u"Thank you for voting!")
            return Response(render("templates/snippets/vote_success.pt", self.response, request = self.request))
        #No vote recieved, continue to render form
        if userid in self.context:
            vote = self.context[userid]
            assert IVote.providedBy(vote)
            appstruct = vote.get_vote_data()
            #Poll might still be open, in that case the poll should be changable
            readonly = not can_vote
            self.response['form'] = form.render(appstruct=appstruct, readonly=readonly)
        #User has not voted
        else:
            readonly = not can_vote
            self.response['form'] = form.render(readonly=readonly)
        return self.response

    @view_config(name = 'modal_poll', context = IPoll, permission = security.VIEW, xhr = True) #
    def poll_view(self):
        """ This is the modal window that opens when you click for instance the vote button
            It will also call the view that renders the actual poll form.
        """
        self.response['poll_plugin'] = self.context.get_poll_plugin()
        self.response['wf_state'] = self.context.get_workflow_state()
        self.response['can_vote'] = self.api.context_has_permission(security.ADD_VOTE, self.context)
        self.response['has_voted'] = self.api.userid in self.context
        self.response['form'] = render('templates/ajax_edit.pt', self.poll_form(), request = self.request)
        result = render('templates/poll_form.pt', self.response, request = self.request)
        if self.request.is_xhr == True:
            result = Response(result)
        return result

    @view_config(context = IPoll, permission = security.VIEW, renderer = "templates/base_edit.pt")
    def poll_full_window(self):
        self.response['form'] = self.poll_view()
        return self.response

    @view_config(context=IPoll, name="poll_raw_data", permission=security.VIEW)
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
