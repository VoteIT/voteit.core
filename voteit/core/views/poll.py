from arche.utils import generate_slug
from arche.views.base import BaseView
from arche.views.base import DefaultAddForm
from arche.views.base import DefaultEditForm
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.traversal import resource_path
from pyramid.view import view_config
from repoze.catalog.query import Eq
from repoze.catalog.query import Any
from voteit.core.portlets.agenda_item import PollsInline
from voteit.core.views.base_inline import PollInlineMixin
from zope.interface.interfaces import ComponentLookupError
import deform

from voteit.core import _
from voteit.core import security
from voteit.core.helpers import get_polls_struct
from voteit.core.models.interfaces import IAgendaItem, IProposal
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.interfaces import IVote


@view_config(context = IPoll,
             name = "poll_raw_data.txt",
             permission = security.VIEW)
class PollRawdataView(BaseView):
    """ View for all ballots. See intefaces.IPollPlugin.render_raw_data
    """

    def __call__(self):
        try:
            poll_plugin = self.context.get_poll_plugin()
        except ComponentLookupError:
            raise HTTPForbidden(_("Poll plugin ${plugin} not found",
                                  mapping = {'plugin': self.context.poll_plugin}))
        if self.context.get_workflow_state() != 'closed':
            raise HTTPForbidden(_("This poll is still open"))
        return poll_plugin.render_raw_data()


@view_config(context = IPoll,
             name = "__show_results__",
             permission = security.VIEW)
class PollResultsView(BaseView):

    def __call__(self):
        try:
            poll_plugin = self.context.get_poll_plugin()
        except ComponentLookupError:
            raise HTTPForbidden(_("Poll plugin ${plugin} not found",
                                  mapping = {'plugin': self.context.poll_plugin}))
        if self.context.get_workflow_state() != 'closed':
            raise HTTPForbidden(_("This poll is still open"))
        return Response(poll_plugin.render_result(self))


@view_config(context = IPoll,
             name = "poll_config",
             renderer = 'arche:templates/form.pt',
             permission = security.EDIT)
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
            self.flash_messages.add(msg, type = 'error')
            raise HTTPFound(location = self.request.resource_url(self.context))
        return super(PollConfigForm, self).__call__()

    def appstruct(self):
        return self.context.poll_settings

    def get_schema(self):
        plugin = _get_poll_plugin(self.context, self.request)
        return plugin.get_settings_schema()

    def save_success(self, appstruct):
        self.context.poll_settings = appstruct
        self.flash_messages.add(self.default_success)
        url = self.request.resource_url(self.context.__parent__, anchor = self.context.uid)
        return HTTPFound(location = url)


@view_config(name = "__vote__",
             context = IPoll,
             renderer = "arche:templates/form.pt",
             permission = security.VIEW)
class PollVoteForm(DefaultEditForm):
    """ Adding and changing a vote object is always done with a poll object as context.
    """
    formid = 'vote_form'
    use_ajax = True
    ajax_options = """
        {success:
          function () {
            voteit.load_target("#ai-polls [data-load-target]");
            voteit.watcher.fetch_data();
          },
        error:
          function (jqxhr) {
            arche.flash_error(jqxhr);
          }
        }
    """

    @property
    def buttons(self):
        buttons = [self.button_cancel]
        if self.can_vote:
            buttons.insert(0, deform.Button('vote', _(u"add_vote_button", default=u"Vote")))
        return buttons

    @property
    def title(self):
        return self.context.title

    @property
    def can_vote(self):
        return self.request.has_permission(security.ADD_VOTE, self.context)

    @property
    def poll_plugin(self):
        return _get_poll_plugin(self.context, self.request)

    @property
    def readonly(self):
        return not self.can_vote

    def get_schema(self):
        return self.poll_plugin.get_vote_schema()

    def appstruct(self):
        if self.request.authenticated_userid in self.context:
            return self.context[self.request.authenticated_userid].get_vote_data()
        return {}

    def vote_success(self, appstruct):
        #Just in case the form rendered before the poll closed
        if not self.can_vote:
            raise HTTPForbidden(_("You're not allowed to vote"))
        Vote = self.poll_plugin.get_vote_class()
        if not IVote.implementedBy(Vote):
            raise TypeError("Poll plugins method get_vote_class returned something that didn't implement IVote.")
        appstruct.pop('csrf_token', None)
        userid = self.request.authenticated_userid
        if userid in self.context:
            vote = self.context[userid]
            assert IVote.providedBy(vote), "%r doesn't provide IVote" % vote
            vote.set_vote_data(appstruct)
            success_msg = _("Your vote was changed.")
        else:
            vote = Vote(creators = [userid])
            #We don't need to send events here, since object added will take care of that
            vote.set_vote_data(appstruct, notify = False)
            #To fire events after set_vote_data is done
            self.context[userid] = vote
            success_msg = _("vote_success_msg",
                            default = "Your vote has been added. If you wish to change it, "
                            "you may do so as long as the poll is open.")
        self.flash_messages.add(success_msg)
        return self._remove_modal_response()

    def _remove_modal_response(self, *args):
        return Response(render("arche:templates/deform/destroy_modal.pt", {}, request = self.request))

    cancel_success = cancel_failure = _remove_modal_response

    def show(self, form):
        appstruct = self.appstruct()
        if appstruct is None:
            appstruct = {}
        return {'form': form.render(appstruct = appstruct, readonly = self.readonly)}


@view_config(context = IAgendaItem,
             name="add",
             renderer='arche:templates/form.pt',
             request_param = "content_type=Poll")
class AddPollForm(DefaultAddForm):

    def save_success(self, appstruct):
        obj = self.request.content_factories[self.type_name](**appstruct)
        name = generate_slug(self.context, appstruct['title'])
        self.context[name] = obj
        #Polls might have a special redirect action if the poll plugin has a settings schema
        if obj.get_poll_plugin().get_settings_schema() is not None:
            url = self.request.resource_url(obj, 'poll_config')
        else:
            url = self.request.resource_url(obj.__parent__, anchor = obj.uid)
        msg = _("private_poll_info",
                default = "The poll is created in private state, to show it the "
                    "participants you have to change the state to upcoming.")
        self.flash_messages.add(msg)
        return HTTPFound(location = url)


@view_config(context = IPoll,
             name = "edit",
             renderer = 'arche:templates/form.pt',
             permission = security.EDIT)
class EditPollForm(DefaultEditForm):

    def save_success(self, appstruct):
        updated = self.context.set_field_appstruct(appstruct)
        plugin_schema = self.context.get_poll_plugin().get_settings_schema()
        plugin_requires_settings = 'poll_plugin' in updated and plugin_schema
        url = self.request.resource_url(self.context.__parent__, anchor=self.context.uid)
        if updated:
            if plugin_requires_settings:
                self.flash_messages.add(_("Update plugin settings"))
                url = self.request.resource_url(self.context, 'poll_config')
            else:
                self.flash_messages.add(_(u"Successfully updated"))
        else:
            self.flash_messages.add(_(u"Nothing changed"))
        return HTTPFound(location = url)


@view_config(context = IPoll,
             name = "edit_proposals",
             renderer = 'arche:templates/form.pt',
             permission = security.EDIT)
class EditPollProposalsForm(DefaultEditForm):
    schema_name = 'edit_proposals'
    title = _("Pick participating proposals")

    def save_success(self, appstruct):
        #Change wf of any removed proposals
        removed_uids = set(self.context.proposals) - set(appstruct['proposals'])
        if removed_uids:
            #Adjust removed proposals back to published state, if they're locked
            for uid in removed_uids:
                prop = self.context.get_proposal_by_uid(uid)
                if prop.get_workflow_state() == 'voting':
                    prop.set_workflow_state(self.request, u'published')
        updated = self.context.set_field_appstruct(appstruct)
        if updated:
            self.flash_messages.add(_(u"Successfully updated"))
        else:
            self.flash_messages.add(_(u"Nothing changed"))
        return HTTPFound(location = self.request.resource_url(self.context))


@view_config(context = IMeeting,
             name = '__polls_menu_content__',
             renderer = 'voteit.core:templates/snippets/polls_menu_content.pt',
             permission = security.VIEW)
class PollsMenuContent(BaseView):
    """ Generate the content of the polls menu in the top right corner.
    """

    def __call__(self):
        response = {}
        response['state_titles'] = self.request.get_wf_state_titles(IPoll, 'Poll')
        response['polls_structure'] = get_polls_struct(self.context, self.request, limit = 5)
        response['vote_perm'] = security.ADD_VOTE
        response['only_link'] = self.context.polls_menu_only_links
        return response


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


@view_config(context=IAgendaItem,
             name='_pick_poll_data.json',
             permission=security.MODERATE_MEETING,
             renderer='json')
class PickPollJSON(BaseView):
    """ Returns json structure with overlays for planning
        which proposals should be in which polls."""

    def __call__(self):
        path = resource_path(self.context)
        query = Eq('path', path) & Eq('type_name', 'Poll') & Any('workflow_state', ('private', 'upcoming'))
        docids = self.request.root.catalog.query(query)[1]
        polls = tuple(self.request.resolve_docids(docids, perm=security.EDIT)) #Must be able to modify poll
        query = Eq('path', path) & Eq('type_name', 'Proposal')
        only_uid = self.request.GET.get('uid', None)
        if only_uid:
            query &= Eq('uid', only_uid)
        docids = self.request.root.catalog.query(query)[1]
        proposals = tuple(self.request.resolve_docids(docids))
        response = {}
        for proposal in proposals:
            values = {'context': proposal, 'polls': polls}
            response[proposal.uid] = render('voteit.core:templates/snippets/pick_polls.pt', values, request=self.request)
        return response


@view_config(context=IPoll,
             name='__set_proposal__',
             permission=security.EDIT,
             renderer='voteit.core:templates/portlets/polls_inline.pt')
class InlineSetProposal(PollsInline, PollInlineMixin):

    def __call__(self):
        selected = bool(self.request.POST.get('selected', None))
        proposal_uid = self.request.POST.get('proposal_uid', '')
        proposals = set(self.context.proposals)
        if selected and proposal_uid not in proposals:
            proposals.add(proposal_uid)
        if not selected and proposal_uid in proposals:
            proposals.remove(proposal_uid)
        self.context.proposals = proposals
        return self.get_context_response()
