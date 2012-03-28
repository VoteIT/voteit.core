import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator


@schema_factory('SiteRootSchema', title = _(u"Edit site root"), description = _(u"Use this form to edit the site root"))
class SiteRootSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
                                title = _(u"Title"),
                                validator=html_string_validator,)
    description = colander.SchemaNode(colander.String(),
                                      title = _(u"Description"),
                                      missing = u"",
                                      widget=deform.widget.RichTextWidget())
    allow_add_meeting = colander.SchemaNode(colander.Boolean(),
                                            title = _(u"Allow authenticated users to add meetings"),
                                            default = False,)

@schema_factory('CaptchaSiteRootSchema', title = _(u"ReCaptcha settings"))
class CaptchaSiteRootSchema(colander.MappingSchema):
    captcha_registration = colander.SchemaNode(colander.Boolean(),
                               title = _(u"Activate recaptcha when registering on the site"),
                                description = _(u"captcha_meeting_checkbox_description",
                                default=u"When this is activated the user is required to fill in a recaptcha when registering on the site"),)
    captcha_meeting = colander.SchemaNode(colander.Boolean(),
                               title = _(u"Activate recaptcha when creating meetings"),
                                description = _(u"captcha_meeting_checkbox_description",
                                default=u"When this is activated the user is required to fill in a recaptcha when creating a meeting"),)
    captcha_public_key = colander.SchemaNode(colander.String(),
                                title = _(u"Public recaptcha key"),
                                validator=html_string_validator,
                                missing=u"")
    captcha_private_key = colander.SchemaNode(colander.String(),
                                title = _(u"Private recaptcha key"),
                                validator=html_string_validator,
                                missing=u"")