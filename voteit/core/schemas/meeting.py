# -*- coding: utf-8 -*-

import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from betahaus.viewcomponent.interfaces import IViewGroup
from pyramid.security import authenticated_userid

from voteit.core.validators import html_string_validator
from voteit.core.widgets import RecaptchaWidget
from voteit.core import VoteITMF as _
from voteit.core import security 

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
    
    settings = request.registry.settings
    
    # Get principals for current user
    principals = api.context_effective_principals(context)
    
    if settings.get('captcha_public_key', None) and settings.get('captcha_private_key', None) and security.ROLE_ADMIN not in principals:
        return RecaptchaWidget()

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
        widget=deform.widget.RichTextWidget())

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
    rss_feed = rss_feed_node();
    access_policy = access_policy_node();
    captcha=recaptcha_node();

@schema_factory('EditMeetingSchema', title = _(u"Edit meeting"))
class EditMeetingSchema(colander.MappingSchema):
    title = title_node();
    description = description_node();
    meeting_mail_name = meeting_mail_name_node();
    meeting_mail_address = meeting_mail_address_node();
    rss_feed = rss_feed_node();
    access_policy = access_policy_node();

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
    rss_feed = rss_feed_node();
    
@schema_factory('AccessPolicyMeetingSchema', title = _(u"Access policy"))
class AccessPolicyeMeetingSchema(colander.MappingSchema):
    access_policy = access_policy_node();