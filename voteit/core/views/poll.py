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
from pyramid.renderers import render
from pyramid.response import Response
from repoze.catalog.query import Any
from repoze.catalog.query import Eq
from repoze.catalog.query import Name
from pyramid.traversal import resource_path

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


_POLL_TEMPLATE = "templates/poll.pt"


class PollView(BaseEdit):
    """ View class for poll objects """
        
    @view_config(context=IPoll, name="edit", renderer='templates/base_edit.pt', permission=EDIT)
    def edit_form(self):
        """ For configuring polls that haven't started yet. """
        schema_name = self.api.get_schema_name(self.context.content_type, 'edit')
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

    def _get_proposal_brains(self, uids):
        query = self.api.root.catalog.query
        get_metadata = self.api.root.catalog.document_map.get_metadata
        ai = find_interface(self.context, IAgendaItem)
        names = {'path': resource_path(ai),
                 'uids': uids}
        num, results = query(Eq('path', Name('path')) \
                             & Eq('content_type', ('Proposal' )) \
                             & Any('uid', Name('uids')), 
                             names = names, sort_index = 'created', reverse = True)
        return [get_metadata(x) for x in results]

    def get_poll_form(self):
        """ Return the Form object that will be used for voting within this poll.
        """
        poll_plugin = self.context.get_poll_plugin()
        schema = poll_plugin.get_vote_schema(self.request, self.api)
        add_csrf_token(self.context, self.request, schema)
        form_id = self.context.__name__
        form = Form(schema,
                    action=resource_url(self.context, self.request),
                    buttons=(button_vote,),
                    formid=form_id,
                    use_ajax=True,
                    ajax_options=
                        """
                        {
                        target: '#booth_%(uid)s .booth.poll',
                        timeout: 10000,
                        beforeSubmit: voteit_poll_beforeSubmit,
                        success: voteit_deform_success,
                        error: function(xhr, status, error) { voteit_poll_error(xhr, status, error, '#booth_%(uid)s'); },
                        complete: function(xhr, textStatus) { voteit_poll_complete(xhr, textStatus); },
                        }
                        """ % {'uid': self.context.uid, 'formid': form_id})
                        #(self.context.uid, self.context.uid))
        #FIXME: This won't work within ajax requests, and we do use ajax now.
        #We need to think about another structure for this
        self.api.register_form_resources(form)
        return form

    @view_config(context=IPoll, renderer=_POLL_TEMPLATE, permission=VIEW)
    def poll_view(self, msg=u""):
        """ Poll view - render the form for voting. This is ment to be fetched from an ajax request,
            but since requests aren't marked as XHR when using IE and deform, it has to render
            a responce regardless. So don't limit loading of this to only ajax!
            The process_poll method does the processing of the data.
        """
        self.response['get_proposal_brains'] = self._get_proposal_brains
        self.response['success_msg'] = msg
        form = self.get_poll_form()
        can_vote = has_permission(ADD_VOTE, self.context, self.request)
        userid = self.api.userid
        if userid in self.context:
            #If editing a vote is allowed, redirect. Editing is only allowed in open polls
            vote = self.context[userid]
            assert IVote.providedBy(vote)
            #show the users vote and edit button
            appstruct = vote.get_vote_data()
            #Poll might still be open, in that case the poll should be changable
            readonly = not can_vote
            self.response['form'] = form.render(appstruct=appstruct, readonly=readonly)
        #User has not voted
        else:
            readonly = not can_vote
            self.response['form'] = form.render(readonly=readonly)
        return self.response

    @view_config(context=IPoll, renderer=_POLL_TEMPLATE, permission=ADD_VOTE, request_method='POST')
    def process_poll(self):
        """ Handles the incoming POST which is the result of a poll form generated by the poll_view.
        """
        self.response['get_proposal_brains'] = self._get_proposal_brains
        post = self.request.POST
        if not 'vote' in post:
            raise HTTPForbidden(u"Process poll expected 'vote'-action - aborting.")
        form = self.get_poll_form()
        controls = post.items()
        try:
            #appstruct is deforms convention. It will be the submitted data in a dict.
            appstruct = form.validate(controls)
        except ValidationFailure, e:
            self.response['form'] = e.render()
            if self.request.is_xhr:
                return Response(render(_POLL_TEMPLATE, self.response, request = self.request))
            #Quirks mode for broken browsers like IE
            error_msg = _(u"bad_browser_validation_error",
                          default = u"There was a validation error when you voted, but since you're using "
                                    u"a browser that doesn't handle standards well (like Internet Explorer) we can't "
                                    u"inline-check your data. Please try again. And we really recommend switching browser.")
            self.api.flash_messages.add(error_msg, type='error')
            url = self.request.resource_url(self.context.__parent__, anchor=self.context.uid)
            return Response(headers = [('X-Relocate', url)])

        poll_plugin = self.context.get_poll_plugin()
        Vote = poll_plugin.get_vote_class()
        if not IVote.implementedBy(Vote):
            raise TypeError("Poll plugins method get_vote_class returned something that didn't implement IVote.")

        #Remove crsf_token from appstruct after validation
        del appstruct['csrf_token']

        userid = self.api.userid
        if userid in self.context:
            vote = self.context[userid]
            assert IVote.providedBy(vote)
            vote.set_vote_data(appstruct)
            success_msg = _(u"Your vote was updated.")
        else:
            vote = Vote(creators = [userid])
            #We don't need to send events here, since object added will take care of that
            vote.set_vote_data(appstruct, notify = False)
            #To fire events after set_vote_data is done
            self.context[userid] = vote
            success_msg = _(u"Thank you for voting!")
        if self.request.is_xhr:
            return self.poll_view(msg = success_msg)
        #This is a "quirks mode" for IE which doesn't set XHR on ajax submit with deform
        self.api.flash_messages.add(success_msg)
        warning_message = _(u"evil_browser_on_vote_notice",
                            default = u"Warning! You're using a browser that doesn't handle standards well (For instance Internet Explorer). "
                                      u"We recommend you review your vote to make sure it got saved, and that you switch to another browser.")
        self.api.flash_messages.add(warning_message, 'warning')
        url = self.request.resource_url(self.context.__parent__, anchor=self.context.uid)
        return Response(headers = [('X-Relocate', url)])

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
