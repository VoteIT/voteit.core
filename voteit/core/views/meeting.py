from arche.views.base import BaseView
from arche.views.base import DefaultEditForm
from betahaus.viewcomponent import render_view_group
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.traversal import resource_path
from pyramid.view import view_config
from pyramid.view import view_defaults
from repoze.catalog.query import Eq
from zope.interface.interfaces import ComponentLookupError

from voteit.core import security
from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.schemas import button_request_access
from voteit.core.models.schemas import button_cancel
from voteit.core.views.base_edit import ArcheFormCompat


@view_defaults(context = IMeeting, permission = security.VIEW)
class MeetingView(BaseView):

    @view_config(renderer="voteit.core:templates/meeting.pt", permission = NO_PERMISSION_REQUIRED)
    def meeting_view(self):
        """ Meeting view behaves a bit differently than regular views since
            it should allow users to request access if unauthorized is raised.
        """
        if not self.request.has_permission(security.VIEW, self.context):
            #We delegate permission checks to the request_meeting_access part.
            url = self.request.resource_url(self.context, 'request_access')
            return HTTPFound(location = url)
        return {}

    @view_config(name = "participants_emails",
                 renderer = "voteit.core:templates/users_emails.pt",
                 permission = security.MODERATE_MEETING)
    def participants_emails(self):
        """ List all participants emails in this meeting. """
        users = self.request.root.users
        results = []
        for userid in security.find_authorized_userids(self.context, (security.VIEW,)):
            user = users.get(userid, None)
            if user:
                results.append(user)
        def _sorter(obj):
            return obj.email
        return {'users': tuple(sorted(results, key = _sorter)), 'title': _("Participants emails")}

    @view_config(name = "minutes", renderer = "voteit.core:templates/minutes.pt", permission = security.VIEW)
    def minutes(self):
        """ Show an overview of the meeting activities. Should work as a template for minutes. """

        if self.request.meeting.get_workflow_state() != 'closed':
            msg = _(u"meeting_not_closed_minutes_incomplete_notice",
                    default = u"This meeting hasn't closed yet so these minutes won't be complete")
            self.flash_messages.add(msg)
        #Add agenda item objects to response
        query = dict(
            path = resource_path(self.context),
            type_name = "AgendaItem",
            workflow_state = ('upcoming', 'ongoing', 'closed'),
            sort_index = "order",
        )
        return {'agenda_items': self.catalog_search(resolve = True, **query)}

    @view_config(name = '__userinfo__', permission = security.VIEW, renderer = "arche:templates/content/basic.pt")
    def userinfo(self):
        """ Special view to allow other meeting participants to see information about a user
            who's in the same meeting as them.
            Normally called via AJAX and included in a popup or similar, but also a part of the
            users profile page.
            
            Note that a user might have participated within a meeting, and after that lost their
            permission. This view has to at least display the username of that person.
        """
        try:
            info_userid = self.request.subpath[0]
        except IndexError:
            info_userid = None
        if not info_userid in security.find_authorized_userids(self.context, (security.VIEW,)):
            msg = _(u"userid_not_registered_within_meeting_error",
                    default = u"Couldn't find any user with userid '${info_userid}' within this meeting.",
                    mapping = {'info_userid': info_userid})
            raise HTTPForbidden( self.request.localizer.translate(msg) )
        user = self.request.root['users'].get(info_userid)
        return {'contents': render_view_group(user, self.request, 'user_info', view = self)}


@view_config(name = "reload_data.json", context = IMeeting, permission = security.VIEW, renderer = 'json')
def reload_data_json(context, request):
    """ A json list of things interesting for an eventual update of agenda items view or poll menu.
        See reload_meeting_data in voteit_common.js

        Note: This is not a smart way of doing this, so MAKE SURE this executes fast!
        This will be replaced when proper websockets are in place.
    """
    root = context.__parent__
    response = {'polls': {}, 'proposals': {}, 'discussionposts': ()}
    #Get poll reload information
    query = Eq('content_type', 'Poll' ) & Eq('path', resource_path(context))
    #ISn't there a smarter way to load wfs?
    for wf_state in ('upcoming', 'ongoing', 'canceled', 'closed'):
        response['polls'][wf_state] = tuple(root.catalog.query(query & Eq('workflow_state', wf_state),
                                                               sort_index = 'created')[1])
    #Fetch proposals and discussions? We'll focus on unread here, polls should catch wf changes on most proposals
    ai_name = request.GET.get('ai_name', None)
    if ai_name and ai_name in context:
        query = Eq('path', resource_path(context, ai_name))
        #Proposal
        #This seems silly too...
        for wf_state in ('published', 'retracted', 'voting', 'approved', 'denied', 'unhandled'):
            response['proposals'][wf_state] = tuple(root.catalog.query(query & Eq('content_type', 'Proposal') \
                                                                       & Eq('workflow_state', wf_state),
                                                                       sort_index = 'created')[1])
        #DiscussionPost
        response['discussionposts'] = tuple(root.catalog.query(query & Eq('content_type', 'DiscussionPost'),
                                                               sort_index = 'created')[1])
    return response


@view_config(context = IMeeting,
             name = "access_policy",
             renderer = "arche:templates/form.pt",
             permission = security.MODERATE_MEETING)
class AccessPolicyForm(ArcheFormCompat, DefaultEditForm):

    schema_name = 'access_policy'

    def save_success(self, appstruct):
        response = super(AccessPolicyForm, self).save_success(appstruct)
        ap = self.request.registry.queryAdapter(self.context,
                                                IAccessPolicy,
                                                name = self.context.get_field_value('access_policy', ''))
        if ap and ap.config_schema():
            self.flash_messages.add(_(u"Review access policy configuration"))
            url = self.request.resource_url(self.context, 'configure_access_policy')
            return HTTPFound(location = url)
        return response


@view_config(context = IMeeting,
             name = "meeting_poll_settings",
             renderer = "arche:templates/form.pt",
             permission = security.MODERATE_MEETING)
class MeetingPollSettingsForm(ArcheFormCompat, DefaultEditForm):

    schema_name = 'meeting_poll_settings'


@view_config(context = IMeeting,
             name = "request_access",
             renderer = "voteit.core:templates/request_meeting_access.pt",
             permission = NO_PERMISSION_REQUIRED)
class RequestAccessForm(ArcheFormCompat, DefaultEditForm):
    """ This page appears when a user clicked on a link to a meeting where the user in question
        don't have access.
        This is controled via access policies. See IAccessPolicy
    """
    buttons = (button_request_access, button_cancel,)
    title = ""

    def appstruct(self):
        return {}

    def get_schema(self):
        schema = self.access_policy.schema()
        if schema is None:
            raise HTTPForbidden(_("You need to contact the moderator to get access to this meeting."))
        return schema

    @reify
    def access_policy(self):
        access_policy_name = self.context.get_field_value('access_policy', '')
        try:
            return self.request.registry.getAdapter(self.context, IAccessPolicy, name = access_policy_name)
        except ComponentLookupError:
            err_msg = _(u"access_policy_not_found",
                        default = u"""Can't find an access policy with the id '${policy}'.
                                    This might mean that the registered access type for this meeting doesn't exist.
                                    Please contact the moderator about this.""",
                        mapping = {'policy': self.context.get_field_value('access_policy', '')})
            raise HTTPForbidden(err_msg)

    def __call__(self):
        if self.request.has_permission(security.VIEW):
            return HTTPFound(location = self.request.resource_url(self.context))
        if not self.request.authenticated_userid:
            msg = _("You need to login or register.")
            self.flash_messages.add(msg, type='info', auto_destruct = False)
            came_from = self.request.resource_url(self.context, 'request_access')
            url = self.request.resource_url(self.root, query={'came_from': came_from})
            return HTTPFound(location = url)
        if self.access_policy.view is not None:
            #Redirect to access policy custom view
            return HTTPFound(location = self.request.resource_url(self.context, self.access_policy.view))
        return super(RequestAccessForm, self).__call__()

    def request_access_success(self, appstruct):
        return self.access_policy.handle_success(self, appstruct)


@view_config(context = IMeeting,
             name = "configure_access_policy",
             renderer = "arche:templates/form.pt",
             permission = security.MODERATE_MEETING)
class ConfigureAccessPolicyForm(ArcheFormCompat, DefaultEditForm):

    @reify
    def access_policy(self):
        access_policy_name = self.context.get_field_value('access_policy', '')
        try:
            return self.request.registry.getAdapter(self.context, IAccessPolicy, name = access_policy_name)
        except ComponentLookupError:
            err_msg = _(u"access_policy_not_found_moderator",
                        default = u"""Can't find an access policy with the id '${policy}'.
                                    This might mean that the registered access policy type for this meeting doesn't exist.
                                    Please change access policy.""",
                        mapping = {'policy': self.context.get_field_value('access_policy', '')})
            raise HTTPForbidden(self.request.localizer.translate(err_msg))

    def get_schema(self):
        return self.access_policy.config_schema()

    def save_success(self, appstruct):
        return self.access_policy.handle_config_success(self, appstruct)
