import urllib

from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config
from zope.interface.interfaces import ComponentLookupError

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core.models.interfaces import IPoll, IAgendaItem
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IVote
from voteit.core.models.schemas import add_came_from
from voteit.core.models.schemas import button_vote
from voteit.core.views.base_edit import BaseEdit
from voteit.core.views.base_edit import DefaultAddForm
from voteit.core.views.base_edit import DefaultEditForm


class PollView(BaseEdit):
    """ View class for poll objects """

    def query_poll_plugin(self, context):
        plugin = self.request.registry.queryAdapter(context, IPollPlugin, context.poll_plugin_name)
        if plugin:
            return plugin
        msg = _(u"poll_plugin_not_found_error",
                default = u"This poll uses a plugin that can't be found. Make sure a poll "
                          u"plugin with the name '${name}' is installed",
                mapping = {'name': context.poll_plugin_name})
        self.api.flash_messages.add(msg, type = 'error')

    @view_config(name = 'modal_poll', context = IPoll, permission = security.VIEW, xhr = True) #
    def poll_view(self):
        """ This is the modal window that opens when you click for instance the vote button
            It will also call the view that renders the actual poll form.
        """
        poll_plugin = self.query_poll_plugin(self.context)
        if not poll_plugin:
            return HTTPForbidden()
        self.response['poll_plugin'] = poll_plugin
        self.response['wf_state'] = self.context.get_workflow_state()
        self.response['can_vote'] = self.api.context_has_permission(security.ADD_VOTE, self.context)
        self.response['has_voted'] = self.api.userid in self.context
        vote_form = PollVoteForm(self.context, self.request)
        self.response['form'] = render('templates/ajax_edit.pt', vote_form(), request = self.request)
        result = render('templates/poll_form.pt', self.response, request = self.request)
        if self.request.is_xhr == True:
            result = Response(result)
        return result

    @view_config(context = IPoll, permission = security.VIEW, renderer = "templates/poll_single.pt")
    def poll_full_window(self):
        self.response['form'] = self.poll_view()
        return self.response

    @view_config(context=IPoll, name="poll_raw_data", permission=security.VIEW)
    def poll_raw_data(self):
        """ View for all ballots. See intefaces.IPollPlugin.render_raw_data
        """
        if self.context.get_workflow_state() != 'closed':
            self.api.flash_messages.add("Poll not closed yet", type='error')
            url = self.request.resource_url(self.context)
            return HTTPFound(location=url)
        poll_plugin = self.query_poll_plugin(self.context)
        if not poll_plugin:
            return HTTPForbidden()
        return poll_plugin.render_raw_data()


@view_config(context=IPoll,
             name="poll_config",
             renderer='templates/base_edit.pt',
             permission=security.EDIT)
class PollConfigForm(DefaultEditForm):
    """ Configure poll settings. Only for moderators.
        The settings themselves come from the poll plugin.
        Note that the Edit permission should only be granted to moderators
        before the actual poll has been set in the ongoing state. After that,
        no settings may be changed.
    """

    def __call__(self):
        if self.schema is None:
            msg = _("No settings for this poll")
            self.api.flash_messages.add(msg, type = 'error')
            raise HTTPFound(location = self.request.resource_url(self.context))
        return super(PollConfigForm, self).__call__()

    def appstruct(self):
        return self.context.poll_settings

    def get_schema(self):
        plugin = _get_poll_plugin(self.context, self.request)
        return plugin.get_settings_schema()

    def save_success(self, appstruct):
        self.context.poll_settings = appstruct
        self.api.flash_messages.add(self.default_success)
        url = self.request.resource_url(self.context.__parent__, anchor = self.context.uid)
        return HTTPFound(location = url)


@view_config(name="_poll_form", context = IPoll, renderer="templates/ajax_edit.pt", permission=security.VIEW, xhr=True)
@view_config(name="_poll_form", context = IPoll, renderer="templates/poll_single.pt", permission=security.VIEW, xhr=False)
class PollVoteForm(DefaultEditForm):
    """ Adding and changing a vote object is always done with a poll object as context.
    """
    buttons = (button_vote,)

    @property
    def form_options(self):
        return {'action': self.request.resource_url(self.context, '_poll_form'),
                'formid': 'vote_form'}

    @property
    def can_vote(self):
        return self.api.context_has_permission(security.ADD_VOTE, self.context)

    @property
    def poll_plugin(self):
        return _get_poll_plugin(self.context, self.request)

    @property
    def readonly(self):
        return not self.can_vote

    def appstruct(self):
        if self.api.userid in self.context:
            return self.context[self.api.userid].get_vote_data()
        return {}

    def get_schema(self):
        return self.poll_plugin.get_vote_schema(self.request, self.api)

    def vote_success(self, appstruct):
        #Just in case the form rendered before the poll closed
        if not self.can_vote:
            raise HTTPForbidden(_("You're not allowed to vote"))
        Vote = self.poll_plugin.get_vote_class()
        if not IVote.implementedBy(Vote):
            raise TypeError("Poll plugins method get_vote_class returned something that didn't implement IVote.")
        appstruct.pop('csrf_token', None)
        userid = self.api.userid
        if userid in self.context:
            vote = self.context[userid]
            assert IVote.providedBy(vote)
            vote.set_vote_data(appstruct)
        else:
            vote = Vote(creators = [userid])
            #We don't need to send events here, since object added will take care of that
            vote.set_vote_data(appstruct, notify = False)
            #To fire events after set_vote_data is done
            self.context[userid] = vote
        success_msg = _(u"Your vote has been registered!")
        if self.request.is_xhr:
            self.response['success_msg'] = success_msg
            return Response(render("templates/snippets/vote_success.pt", self.response, request = self.request))
        self.api.flash_messages.add(success_msg)
        url = self.request.resource_url(self.context.__parent__, anchor = self.context.uid)
        return HTTPFound(location = url)


@view_config(context=IAgendaItem, name="add", renderer='templates/base_edit.pt', request_param = "content_type=Poll")
class AddPollForm(DefaultAddForm):

    def add_success(self, appstruct):
        #Don't save this data
        add_reject_proposal = appstruct.pop('add_reject_proposal', None)
        reject_proposal_title = appstruct.pop('reject_proposal_title', None)

        if add_reject_proposal:
            reject_proposal = createContent('Proposal', title = reject_proposal_title)
            name = reject_proposal.suggest_name(self.context)
            self.context[name] = reject_proposal
            appstruct['proposals'].add(reject_proposal.uid)

        obj = createContent(self.content_type, **appstruct)
        name = obj.suggest_name(self.context)
        self.context[name] = obj

        #Polls might have a special redirect action if the poll plugin has a settings schema
        if obj.get_poll_plugin().get_settings_schema() is not None:
            url = self.request.resource_url(obj, 'poll_config')
        else:
            url = self.request.resource_url(obj.__parent__, anchor = obj.uid)
        msg = _("private_poll_info",
                default = "The poll is created in private state, to show it the "
                    "participants you have to change the state to upcoming.")
        self.api.flash_messages.add(msg)
        return HTTPFound(location = url)


@view_config(context = IPoll,
             name = "edit",
             renderer = 'templates/base_edit.pt',
             permission = security.EDIT)
class EditPollForm(DefaultEditForm):

    def get_schema(self):
        schema_name = self.api.get_schema_name(self.context.content_type, 'edit')
        schema = createSchema(schema_name)
        add_came_from(self.context, self.request, schema)
        return schema

    def save_success(self, appstruct):
        came_from = appstruct.pop('came_from', None)
        if came_from:
            url = urllib.unquote(came_from)
        else:
            url = self.request.resource_url(self.context.__parent__, anchor = self.context.uid)
        #Change wf of any removed proposals
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
        return HTTPFound(location = url)


def _get_poll_plugin(context, request):
    assert IPoll.providedBy(context), "Not a poll object"
    try:
        return request.registry.getAdapter(context, IPollPlugin, context.poll_plugin_name)
    except ComponentLookupError:
        msg = _(u"poll_plugin_not_found_error",
                default = u"This poll uses a plugin that can't be found. Make sure a poll "
                          u"plugin with the name '${name}' is installed",
                mapping = {'name': context.poll_plugin_name})
        raise HTTPForbidden(msg)
