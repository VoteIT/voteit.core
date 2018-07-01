# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.validators import existing_userids
from arche.schemas import userid_hinder_widget
from repoze.catalog.query import Eq, NotEq
import colander
import deform

from voteit.core import _
from voteit.core import security
from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IProposal
from voteit.core.schemas.common import NAME_PATTERN
from voteit.core.validators import no_html_validator
from voteit.core.validators import richtext_validator
from voteit.core.validators import TagValidator


@colander.deferred
def deferred_access_policy_widget(node, kw):
    request = kw['request']
    choices = [(x.name, x.factory) for x in request.registry.registeredAdapters() if
               x.provided == IAccessPolicy]
    return deform.widget.RadioChoiceWidget(values=choices,
                                           template="object_radio_choice",
                                           readonly_template="readonly/object_radio_choice")


def _get_meetings_that_could_be_copied(request, context):
    """ Returns any meetings that could be copied (in one or another way) in this context.
        - If meeting is context, make sure that isn't included
        - Make sure the logged in user has the moderate meeting perm.
    """
    docids = request.root.catalog.query(
        Eq('type_name', 'Meeting') & NotEq('uid', context.uid),
        sort_index='sortable_title',
    )[1]
    return request.resolve_docids(docids, perm=security.MODERATE_MEETING)


@colander.deferred
def deferred_copy_from_meeting_widget(node, kw):
    request = kw['request']
    context = kw['context']
    choices = [('', _("<Select>"))]
    for meeting in _get_meetings_that_could_be_copied(request, context):
        choices.append((meeting.__name__, "%s (%s)" % (meeting.title, meeting.__name__)))
    return deform.widget.SelectWidget(values=choices)


@colander.deferred
def deferred_current_user_mail(node, kw):
    request = kw['request']
    if request.profile:
        return request.profile.email


@colander.deferred
def _deferred_current_fullname(node, kw):
    request = kw['request']
    if request.profile:
        return request.profile.title


class MeetingSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Title"),
        description=_("meeting_title_description",
                      default="Set a title for the meeting that separates it from previous meetings"),
        validator=no_html_validator,
    )
    meeting_mail_name = colander.SchemaNode(
        colander.String(),
        title=_("Name of the contact person for this meeting"),
        default=_deferred_current_fullname,
        validator=colander.Regex(regex=NAME_PATTERN,
                                 msg=_("name_pattern_error",
                                       default="Must be at least 3 chars + only alphanumeric characters allowed")),
    )
    meeting_mail_address = colander.SchemaNode(
        colander.String(),
        title=_("Contact email for this site"),
        default=deferred_current_user_mail,
        validator=colander.All(
            colander.Email(msg=_("Invalid email address.")),
            no_html_validator, ),
    )
    description = colander.SchemaNode(
        colander.String(),
        title=_("Short description"),
        description=_("short_description_text",
                      default="Shows up in search results and similar. One sentence is enough. "
                              "You don't need to add it if you don't want to."),
        missing="",
        validator=no_html_validator
    )
    body = colander.SchemaNode(
        colander.String(),
        title=_("Participants description"),
        description=_("meeting_description_description",
                      default="This is only visible to participants, so don't put information on how to register here. "
                              "Displayed on the first page of the meeting. You can include things "
                              "like information about the meeting, how to contact the moderator and your logo."),
        missing="",
        widget=deform.widget.RichTextWidget(
            options=(('theme', 'advanced'),)),
        validator=richtext_validator,
    )
    public_description = colander.SchemaNode(
        colander.String(),
        title=_("Public presentation"),
        description=_("meeting_public_description_description",
                      default="The public description is visible on the request access "
                              "page and to not yet logged in visitors."),
        missing="",
        widget=deform.widget.RichTextWidget(options=(('theme', 'advanced'),)),
        validator=richtext_validator, )
    hide_meeting = colander.SchemaNode(
        colander.Bool(),
        title=_("Hide meeting from listings"),
        description=_("hide_meeting_description",
                      default="Users won't be able to find it unless they have a link to it."),
        tab='advanced',
        default=False,
        missing=False
    )
    nav_title = colander.SchemaNode(
        colander.String(),
        title=_("Navigation bar title"),
        description=_(
            "In case you want another title in the navigation bar"),
        missing="",
        tab='advanced'
    )


class EditMeetingSchema(MeetingSchema):
    pass


class AddMeetingSchema(MeetingSchema):
    pass


class CopyUserPermsSchema(colander.Schema):
    meeting_name = colander.SchemaNode(
        colander.String(),
        title=_("Copy users and permissions from a previous meeting."),
        description=_("copy_users_and_perms_description",
                      default="You can only pick meeting where you've been a moderator. "
                              "Note that permissions are addative, so nothing will be removed."),

        widget=deferred_copy_from_meeting_widget,
    )


_TYPES_CHOICES = (
    ('DiscussionPost', _("Discussion Post")),
    ('Proposal', _("Proposal")),
)


@colander.deferred
def prop_states_choice(node, kw):
    request = kw['request']
    results = request.get_wf_state_titles(IProposal, 'Proposal')
    values = []
    for (k, v) in results.items():
        values.append((k, v))
    return deform.widget.CheckboxChoiceWidget(values=values)


class CopyAgendaSchema(colander.Schema):
    meeting_name = colander.SchemaNode(
        colander.String(),
        title=_("Copy Agenda from a previous meeting."),
        description=_("You can only pick meeting where you've been a moderator. "),
        widget=deferred_copy_from_meeting_widget,
    )
    copy_types = colander.SchemaNode(
        colander.Set(),
        title=_("Copy these types"),
        missing=(),
        default=[x[0] for x in _TYPES_CHOICES],
        widget=deform.widget.CheckboxChoiceWidget(values=_TYPES_CHOICES)
    )
    only_copy_prop_states = colander.SchemaNode(
        colander.Set(),
        title=_("Only copy proposals in these states"),
        missing=(),
        default=('published', 'approved', 'denied'),
        widget=prop_states_choice,
    )
    all_props_published = colander.SchemaNode(
        colander.Bool(),
        title = _("Make all proposals published?"),
        description = _("Uncheck this to retain workflow state")
    )


class AccessPolicyMeetingSchema(colander.MappingSchema):
    access_policy = colander.SchemaNode(
        colander.String(),
        title=_("Meeting access policy"),
        widget=deferred_access_policy_widget,
        default="invite_only",
    )


class _ContainsOnlyAndNotEmpty(colander.ContainsOnly):
    def __call__(self, node, value):
        if len(value) == 0:
            raise colander.Invalid(node, _("Must select at least one"))
        return super(_ContainsOnlyAndNotEmpty, self).__call__(node, value)


_DEFAULT_ROLES = {
    security.ROLE_VIEWER,
    security.ROLE_DISCUSS,
    security.ROLE_PROPOSE,
    security.ROLE_VOTER,
}


class AddExistingUserSchema(colander.Schema):
    userid = colander.SchemaNode(
        colander.String(),
        title=_("UserID"),
        widget=userid_hinder_widget,
        validator=existing_userids
    )
    roles = colander.SchemaNode(
        colander.Set(),
        title=_("Roles"),
        default=_DEFAULT_ROLES,
        validator=_ContainsOnlyAndNotEmpty(dict(security.MEETING_ROLES).keys()),
        widget=deform.widget.CheckboxChoiceWidget(values=security.MEETING_ROLES)
    )


_BULK_CHOICES = (
    ('', _("Don't change")),
    ('add', _("Give to all")),
    ('remove', _("Remove from all")),
)


def bulk_change_roles_widget():
    return deform.widget.SelectWidget(values=_BULK_CHOICES)


_BULK_VALIDATOR = colander.OneOf(('', 'add', 'remove'))


class BulkChangeRolesSchema(colander.Schema):
    viewer = colander.SchemaNode(
        colander.String(),
        title = security.ROLE_VIEWER.title,
        widget = bulk_change_roles_widget(),
        validator=_BULK_VALIDATOR,
        missing="",
    )
    discuss = colander.SchemaNode(
        colander.String(),
        title = security.ROLE_DISCUSS.title,
        widget = bulk_change_roles_widget(),
        validator=_BULK_VALIDATOR,
        missing="",
    )
    propose = colander.SchemaNode(
        colander.String(),
        title = security.ROLE_PROPOSE.title,
        widget = bulk_change_roles_widget(),
        validator=_BULK_VALIDATOR,
        missing="",
    )
    voter = colander.SchemaNode(
        colander.String(),
        title = security.ROLE_VOTER.title,
        widget = bulk_change_roles_widget(),
        validator=_BULK_VALIDATOR,
        missing="",
    )


class AgendaLabelsSchema(colander.Schema):
    #Note on name: tags is an existing property in the catalog.
    #It does however only index lowercase version of things
    #keep that in mind while searching!
    tags = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.String(),
            title = _("label"),
            name='notused',
            validator=TagValidator(),
        ),
        title = _("agenda_labels_schema_title",
            default="Adding labels here will make them selectable on agenda items. "
                  "They'll also appear as a sorting option in the agenda."),
    )


class NotificationSettingsSchema(colander.Schema):
    mention_notification_setting = colander.SchemaNode(
        colander.Bool(),
        title=_("Send mail to mentioned users."),
        default=True,
        missing=True,
    )
    poll_notification_setting = colander.SchemaNode(
        colander.Bool(),
        title=_(
            "Send mail to voters when a poll starts."),
        default=False,
        missing=False,
    )


def includeme(config):
    config.add_schema('Meeting', AddMeetingSchema, 'add')
    config.add_schema('Meeting', EditMeetingSchema, 'edit')
    config.add_schema('Meeting', CopyUserPermsSchema, 'copy_users_perms')
    config.add_schema('Meeting', CopyAgendaSchema, 'copy_agenda')
    config.add_schema('Meeting', AccessPolicyMeetingSchema, 'access_policy')
    config.add_schema('Meeting', AddExistingUserSchema, 'add_existing_user')
    config.add_schema('Meeting', BulkChangeRolesSchema, 'bulk_change_roles')
    config.add_schema('Meeting', AgendaLabelsSchema, 'agenda_labels')
    config.add_schema('Meeting', NotificationSettingsSchema, 'notification_settings')
