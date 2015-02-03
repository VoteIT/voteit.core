# -*- coding: utf-8 -*-

import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core import security 
from voteit.core.models.arche_compat import createContent
from voteit.core.models.interfaces import IAccessPolicy
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.models.meeting import Meeting
from voteit.core.schemas.common import NAME_PATTERN
from voteit.core.validators import html_string_validator
from voteit.core.validators import richtext_validator


@colander.deferred
def poll_plugins_choices_widget(node, kw):
    request = kw['request']
    #Add all selectable plugins to schema. This chooses the poll method to use
    plugin_choices = set()
    #FIXME: The new object should probably be sent to construct schema
    #for now, we can fake this
    fake_poll = createContent('Poll')
    for (name, plugin) in request.registry.getAdapters([fake_poll], IPollPlugin):
        plugin_choices.add((name, plugin.title))
    return deform.widget.CheckboxChoiceWidget(values=plugin_choices)

@colander.deferred
def deferred_access_policy_widget(node, kw):
    request = kw['request']
    choices = []
    for (name, plugin) in request.registry.getAdapters([_dummy_meeting], IAccessPolicy):
        choices.append((name, plugin))
    return deform.widget.RadioChoiceWidget(values = choices, template = "widgets/object_radio_choice", readonly_template = "widgets/readonly/object_radio_choice")


@colander.deferred
def deferred_copy_perms_widget(node, kw):
    context = kw['context']
    request = kw['request']
    view = kw['view']
    choices = [('', _(u"<Don't copy>"))]
    for meeting in view.root.get_content(content_type = 'Meeting'):
        if request.has_permission(security.MODERATE_MEETING, meeting):
            choices.append((meeting.__name__, "%s (%s)" % (meeting.title, meeting.__name__)))
    return deform.widget.SelectWidget(values=choices)

@colander.deferred
def deferred_current_user_mail(node, kw):
    view = kw['view']
    if view.profile:
        return view.profile.get_field_value('email')

def title_node():
    return colander.SchemaNode(colander.String(),
                                title = _(u"Title"),
                                description = _(u"meeting_title_description",
                                                default=u"Set a title for the meeting that separates it from previous meetings"),
                                validator=html_string_validator,)
def description_node():
    return colander.SchemaNode(
        colander.String(),
        title = _(u"Participants description"),
        description = _(u"meeting_description_description",
                        default=u"This is only visible to participants, so don't put information on how to register here. "
                            u"Displayed on the first page of the meeting. You can include things "
                            u"like information about the meeting, how to contact the moderator and your logo."),
        missing = u"",
        widget=deform.widget.RichTextWidget(options = (('theme', 'advanced'),)),
        validator=richtext_validator,)

def public_description_node():
    return colander.SchemaNode(
        colander.String(),
        title = _(u"Public presentation"),
        description = _(u"meeting_public_description_description",
                        default=u"The public description is visible on the request access "
                            u"page and to not yet logged in visitors."),
        missing = u"",
        widget=deform.widget.RichTextWidget(options = (('theme', 'advanced'),)),
        validator=richtext_validator,)

@colander.deferred
def _deferred_current_fullname(node, kw):
    view = kw['view']
    if view.profile:
        return view.profile.title

def meeting_mail_name_node():
    return colander.SchemaNode(colander.String(),
                               title = _(u"Name of the contact person for this meeting"),
                               default = _deferred_current_fullname,
                               validator = colander.Regex(regex=NAME_PATTERN,
                                                          msg=_(u"name_pattern_error",
                                                                default = u"Must be at least 3 chars + only alphanumeric characters allowed")),)

def meeting_mail_address_node():
    return colander.SchemaNode(colander.String(),
                               title = _(u"Contact email for this site"),
                               default = deferred_current_user_mail,
                               validator = colander.All(colander.Email(msg = _(u"Invalid email address.")), html_string_validator,),)

def access_policy_node():
    return colander.SchemaNode(colander.String(),
                               title = _(u"Meeting access policy"),
                               widget = deferred_access_policy_widget,
                               default = "invite_only",)

def mention_notification_setting_node():
    return colander.SchemaNode(colander.Bool(),
                               title = _(u"Send mail to mentioned users."),
                               default = True,
                               missing = True)

def poll_notification_setting_node():
    return colander.SchemaNode(colander.Bool(),
                               title = _(u"Send mail to voters when a poll starts."),
                               default = True,
                               missing = True)


@schema_factory('AddMeetingSchema', title = _(u"Add meeting"))
class AddMeetingSchema(colander.MappingSchema):
    title = title_node()
    meeting_mail_name = meeting_mail_name_node()
    meeting_mail_address = meeting_mail_address_node()
    description = description_node()
    public_description = public_description_node()
    access_policy = access_policy_node()
    mention_notification_setting = mention_notification_setting_node()
    poll_notification_setting = poll_notification_setting_node()
    copy_users_and_perms = colander.SchemaNode(colander.String(),
                                               title = _(u"Copy users and permissions from a previous meeting."),
                                               description = _(u"You can only pick meeting where you've been a moderator."),
                                               widget = deferred_copy_perms_widget,
                                               default = u"",
                                               missing = u"")


@schema_factory('EditMeetingSchema', title = _(u"Edit meeting"))
class EditMeetingSchema(colander.MappingSchema):
    title = title_node()
    description = description_node()
    public_description = public_description_node()
    meeting_mail_name = meeting_mail_name_node()
    meeting_mail_address = meeting_mail_address_node()


@schema_factory('PresentationMeetingSchema',
                title = _(u"Presentation"),
                description = _(u"presentation_meeting_schema_main_description",
                                default = u"Edit the first page of the meeting into an informative and pleasant page for your users. "
                                    "You can for instance place your logo here. The time table can be presented in a table and updated as you go along. "
                                    "It's also advised to add links to the manual and to meeting documents."))
class PresentationMeetingSchema(colander.MappingSchema):
    title = title_node()
    description = description_node()
    public_description = public_description_node()


@schema_factory('MailSettingsMeetingSchema', title = _(u"Mail settings"))
class MailSettingsMeetingSchema(colander.MappingSchema):
    meeting_mail_name = meeting_mail_name_node()
    meeting_mail_address = meeting_mail_address_node()
    mention_notification_setting = mention_notification_setting_node()
    poll_notification_setting = poll_notification_setting_node()


@schema_factory('AccessPolicyMeetingSchema', title = _(u"Access policy"))
class AccessPolicyeMeetingSchema(colander.MappingSchema):
    access_policy = access_policy_node()


@schema_factory('MeetingPollSettingsSchema', title = _(u"Poll settings"),
                description = _(u"meeting_poll_settings_main_description",
                                default = u"Settings for the whole meeting."))
class MeetingPollSettingsSchema(colander.MappingSchema):
    poll_plugins = colander.SchemaNode(colander.Set(),
                                       title = _(u"mps_poll_plugins_title",
                                                 default = u"Available poll methods within this meeting"),
                                       description = _(u"mps_poll_plugins_description",
                                                       default=u"Only poll methods selected here will be available withing the meeting. "
                                                               u"If nothing is selected, only the servers default poll method will be available."),
                                       missing=set(),
                                       widget = poll_plugins_choices_widget,)

_dummy_meeting = Meeting()


class AgendaItemProposalsPortletSchema(colander.Schema):
    hide_retracted = colander.SchemaNode(colander.Boolean(),
                                   title = _(u"Hide retracted proposals"),
                                   description = _(u"meeting_hide_retracted_description",
                                                   default=u"You can still access hidden proposals "
                                                      u"by using a collapsible link below the regular proposals."),)
    hide_unhandled_proposals = colander.SchemaNode(colander.Boolean(),
        title = _(u"Hide unhandled proposals"),
        description = _(u"meeting_hide_unhandled_description",
                        default=u"In the same fashion as retracted proposals."),
        default = True,
        missing = True)


def includeme(config):
    config.add_content_schema('Meeting', AddMeetingSchema, 'add')
    config.add_content_schema('Meeting', EditMeetingSchema, 'edit')
