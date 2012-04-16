# -*- coding: utf-8 -*-

import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from betahaus.pyracont.factories import createContent
from betahaus.viewcomponent.interfaces import IViewGroup
from pyramid.security import authenticated_userid

from voteit.core.validators import html_string_validator
from voteit.core.validators import richtext_validator

from voteit.core import VoteITMF as _
from voteit.core import security 
from voteit.core.models.interfaces import IPoll
from voteit.core.models.interfaces import IPollPlugin
from voteit.core.widgets import RecaptchaWidget

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
    view_group = request.registry.getUtility(IViewGroup, name = 'request_meeting_access')
    choices = []
    for (name, va) in view_group.items():
        choices.append((name, va.title))
    if not choices:
        raise ValueError("Can't find anything in the request_meeting_access view group. There's no way to select any policy on how to gain access to the meeting.")
    return deform.widget.RadioChoiceWidget(values = choices)

@colander.deferred
def deferred_recaptcha_widget(node, kw):
    """ No recaptcha if captcha settings is now present or if the current user is an admin 
    """
    context = kw['context']
    request = kw['request']
    api = kw['api']
    
    # Get principals for current user
    principals = api.context_effective_principals(context)
    
    if api.root.get_field_value('captcha_meeting', False) and security.ROLE_ADMIN not in principals:
        pub_key = api.root.get_field_value('captcha_public_key', '')
        priv_key = api.root.get_field_value('captcha_private_key', '')
        return RecaptchaWidget(captcha_public_key = pub_key,
                               captcha_private_key = priv_key)

    return deform.widget.HiddenWidget()

def title_node():
    return colander.SchemaNode(colander.String(),
                                title = _(u"Title"),
                                description = _(u"meeting_title_description",
                                                default=u"Set a title for the meeting that separates it from previous meetings"),
                                validator=html_string_validator,)
def description_node():
     return colander.SchemaNode(
        colander.String(),
        title = _(u"Description"),
        description = _(u"meeting_description_description",
                        default=u"The description is visible on the first page of the meeting. You can include things like information about the meeting, how to contact the moderator and your logo."),
        missing = u"",
        widget=deform.widget.RichTextWidget(),
        validator=richtext_validator,)

def meeting_mail_name_node():
    return colander.SchemaNode(colander.String(),
                               title = _(u"Name visible on system mail sent from this meeting"),
                               default = _(u"VoteIT"),
                               validator = colander.Regex(regex=u'^[\w\sÅÄÖåäö]+$', msg=_(u"Only alphanumeric characters allowed")),)

def meeting_mail_address_node():
    return colander.SchemaNode(colander.String(),
                               title = _(u"Email address to send from"),
                               default = u"noreply@somehost.voteit",
                               validator = colander.All(colander.Email(msg = _(u"Invalid email address.")), html_string_validator,),)
    
def rss_feed_node():
    return colander.SchemaNode(colander.Boolean(),
                               title = _(u"Activate RSS feed"),
								description = _(u"rss_feed_checkbox_description",
								default=u"When the checkbox below is checked your meeting will be able to show a public RSS feed that can be followed with a RSS reader. This feed will contain info about when changes are made in the meeting and who did the changes. You can access the feed on: 'The meeting URL' + '/feed'. This should be something like 'www.yourdomain.com/yourmeetingname/feed'. If you want the feed to show up in an iframe you can use '/framefeed' instead. This is an advanced feature and read more about it in the manual on wiki.voteit.se. Please note a word of warning: the feed is public for all who can figure it out."),


                               default = False,)

def access_policy_node():
    return colander.SchemaNode(colander.String(),
                               title = _(u"Meeting access policy"),
                               widget = deferred_access_policy_widget,
                               default = "invite_only",)
    
    
def recaptcha_node():
    return colander.SchemaNode(colander.String(),
                               #FIXME: write a good title and description here
                               title=_(u"Verify you are human"),
                               description = _(u"meeting_captcha_description",
                                               default=u"This is to prevent spambots from creating meetings"),
                               missing=u"",
                               widget=deferred_recaptcha_widget,)


@schema_factory('AddMeetingSchema', title = _(u"Add meeting"))
class AddMeetingSchema(colander.MappingSchema):
    title = title_node();
    description = description_node();
    meeting_mail_name = meeting_mail_name_node();
    meeting_mail_address = meeting_mail_address_node();
    access_policy = access_policy_node();
    captcha=recaptcha_node();

@schema_factory('EditMeetingSchema', title = _(u"Edit meeting"))
class EditMeetingSchema(colander.MappingSchema):
    title = title_node();
    description = description_node();
    meeting_mail_name = meeting_mail_name_node();
    meeting_mail_address = meeting_mail_address_node();
    access_policy = access_policy_node();
    
@schema_factory('RssSettingsMeetingSchema', title = _(u"RSS settings"))
class RssSettingsMeetingSchema(colander.MappingSchema):
    rss_feed = rss_feed_node();

@schema_factory('PresentationMeetingSchema',
                title = _(u"Presentation"),
                description = _(u"presentation_meeting_schema_main_description",
                                default = u"Edit the first page of the meeting into an informative and pleasant page for your users. You can for instance place your logo here. The time table can be presented in a table and updated as you go along. It's also advised to add links to the manual and to meeting documents."))
class PresentationMeetingSchema(colander.MappingSchema):
    title = title_node();
    description = description_node();
    
@schema_factory('MailSettingsMeetingSchema', title = _(u"Mail settings"))
class MailSettingsMeetingSchema(colander.MappingSchema):
    meeting_mail_name = meeting_mail_name_node();
    meeting_mail_address = meeting_mail_address_node();
    
@schema_factory('AccessPolicyMeetingSchema', title = _(u"Access policy"))
class AccessPolicyeMeetingSchema(colander.MappingSchema):
    access_policy = access_policy_node();
    
@schema_factory('AdvancedSettingsMeetingSchema', title = _(u"Advanced settings"))
class AdvancedSettingsMeetingSchema(colander.MappingSchema):
    poll_plugins = colander.SchemaNode(deform.Set(allow_empty=True),
                                      title = _(u"Available poll method in this meeting"),
                                      description = _(u"meeting_available_poll_plugins_description",
                                                      default=u""),
                                      missing=set(),
                                      widget = poll_plugins_choices_widget,)