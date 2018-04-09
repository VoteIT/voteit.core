from uuid import uuid4

import deform
from arche.events import ObjectUpdatedEvent
from arche.events import SchemaCreatedEvent
from arche.utils import copy_recursive
from arche.utils import generate_slug
from arche.views.base import BaseView
from arche.views.base import DefaultEditForm
from betahaus.viewcomponent import render_view_group
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.view import view_defaults
from six import text_type
from zope.component.event import objectEventNotify
from zope.interface.interfaces import ComponentLookupError

from voteit.core import _
from voteit.core import security
from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.views.base_edit import ArcheFormCompat
from voteit.core.security import unrestricted_wf_transition_to


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

    @view_config(name = "minutes",
                 renderer = "voteit.core:templates/minutes.pt",
                 permission = security.VIEW)
    def minutes(self):
        """ Show an overview of the meeting activities. Should work as a template for minutes. """
        if self.request.meeting.get_workflow_state() != 'closed':
            msg = _(u"meeting_not_closed_minutes_incomplete_notice",
                    default = u"This meeting hasn't closed yet so these minutes won't be complete")
            self.flash_messages.add(msg)
        #Add agenda item objects to response
        results = []
        for obj in self.context.values():
            if IAgendaItem.providedBy(obj) and self.request.has_permission(security.VIEW, obj):
                results.append(obj)
        return {'agenda_items': results}

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


@view_config(context = IMeeting,
             name = "access_policy",
             renderer = "arche:templates/form.pt",
             permission = security.MODERATE_MEETING)
class AccessPolicyForm(ArcheFormCompat, DefaultEditForm):
    schema_name = 'access_policy'
    title = _("Select access policy")

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
             name = "request_access",
             renderer = "voteit.core:templates/request_meeting_access.pt",
             permission = NO_PERMISSION_REQUIRED)
class RequestAccessForm(ArcheFormCompat, DefaultEditForm):
    """ This page appears when a user clicked on a link to a meeting where the user in question
        don't have access.
        This is controled via access policies. See IAccessPolicy
    """
    title = ""

    @property
    def buttons(self):
        return (deform.Button('request_access', _(u"Request access")), self.button_cancel,)

    def appstruct(self):
        return {}

    def get_schema(self):
        schema = self.access_policy.schema()
        if schema is None:
            raise HTTPForbidden(_("forbidden_on_closed_meetings",
                                  default = "You need to contact the moderator "
                                  "to get access to this meeting."))
        objectEventNotify(SchemaCreatedEvent(schema))
        return schema

    @reify
    def access_policy(self):
        access_policy_name = self.context.get_field_value('access_policy', '')
        if not access_policy_name:
            access_policy_name = 'invite_only'
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
            self.flash_messages.add(msg, type='danger', auto_destruct = False)
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
    title = _("Configure access policy")

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


@view_config(context = IMeeting,
             name = "agenda_labels",
             renderer = "arche:templates/form.pt",
             permission = security.MODERATE_MEETING)
class MeetingTagsForm(DefaultEditForm): #ArcheFormCompat?
    schema_name='agenda_labels'
    title = _("Agenda sorting labels")


@view_config(context=IMeeting,
             name="copy_users_perms",
             renderer="arche:templates/form.pt",
             permission=security.MODERATE_MEETING)
class CopyUsersPermsForm(DefaultEditForm):
    schema_name = 'copy_users_perms'
    title = _("Copy users permissions")

    def save_success(self, appstruct):
        from_meeting = self.request.root[appstruct['meeting_name']]
        assert IMeeting.providedBy(from_meeting)
        for (userid, roles) in from_meeting.local_roles.items():
            self.context.local_roles.add(userid, roles, event=False)
        event_obj = ObjectUpdatedEvent(self.context, changed=['local_roles'])
        objectEventNotify(event_obj)
        return HTTPFound(location=self.request.resource_url(self.context))


@view_config(context=IMeeting,
             name="copy_agenda",
             renderer="arche:templates/form.pt",
             permission=security.MODERATE_MEETING)
class CopyAgendaForm(DefaultEditForm):
    schema_name = 'copy_agenda'
    title = _("Copy agenda")

    def save_success(self, appstruct):
        from_meeting = self.request.root[appstruct['meeting_name']]
        reset_wf =  appstruct['all_props_published']
        only_copy_prop_states = appstruct['only_copy_prop_states']
        copy_types = appstruct['copy_types']
        assert IMeeting.providedBy(from_meeting)
        counter = 0
        for ai in from_meeting.values():
            if not IAgendaItem.providedBy(ai):
                continue
            counter += copy_ai(self.context, ai, reset_wf=reset_wf, only_copy_prop_states=only_copy_prop_states, copy_types=copy_types)
        self.flash_messages.add(_("Copied ${num} objects", mapping={'num': counter}))
        return HTTPFound(location=self.request.resource_url(self.context))


def copy_ai(new_parent, ai, reset_wf=False, only_copy_prop_states=(), copy_types=()):
    """
    :param new_parent: The new meeting object
    :param ai: object to be copied
    :param reset_wf: turn all proposals published? (bool)
    :param only_copy_prop_states: (list of states)
    :param copy_types: Copy these types, remove everything else.
    :return:
    """
    # Note about copy: use zope.copy functions, check arche method 'copy_recursive' for that.
    new_ai = copy_recursive(ai)
    new_ai.state = unicode('private')
    counter = 1 #The current ai
    name = generate_slug(new_parent, new_ai.title)
    new_parent[name] = new_ai
    #Create new keys tuple to avoid changing lazy objects during iteration
    for key in tuple(new_ai.keys()):
        obj = new_ai[key]
        type_name = getattr(obj, 'type_name', '')
        if type_name not in copy_types:
            del new_ai[obj.__name__]
            continue
        if type_name == 'Proposal' and obj.get_workflow_state() not in only_copy_prop_states:
            del new_ai[obj.__name__]
            continue
        if reset_wf and obj.type_name == 'Proposal' and obj.get_workflow_state() != 'published':
            unrestricted_wf_transition_to(obj, 'published')
        # Kill anything else contained
        for k in obj.keys():
            del obj[k]
        counter += 1
    return counter
