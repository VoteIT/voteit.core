import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator
from voteit.core.validators import richtext_validator


@schema_factory('SiteRootSchema', title = _(u"Edit site root"), description = _(u"Use this form to edit the site root"))
class SiteRootSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
                                title = _(u"Title"),
                                validator=html_string_validator,)
    description = colander.SchemaNode(colander.String(),
                                      title = _(u"Description"),
                                      missing = u"",
                                      widget=deform.widget.RichTextWidget(),
                                      validator=richtext_validator,)
    site_title = colander.SchemaNode(colander.String(),
                                title = _(u"Site title"),
                                description = _(u"Displayed in the header when you're not in a meeting. Keep it short!"),
                                validator=html_string_validator,)
    footer = colander.SchemaNode(colander.String(),
                                      title = _(u"Footer"),
                                      missing = u"",
                                      widget=deform.widget.RichTextWidget(),
                                      validator=richtext_validator,)
    registration_info = colander.SchemaNode(colander.String(),
                                      title = _(u"Registration info"),
                                      description = _(u"site_root_registration_info_description",
                                                      default = u"Information displayed on the registration page, right hand side."),
                                      missing = u"",
                                      widget=deform.widget.RichTextWidget(),
                                      validator=richtext_validator,)
    allow_add_meeting = colander.SchemaNode(colander.Boolean(),
                                            title = _(u"Allow authenticated users to add meetings"),
                                            default = False,)


@schema_factory('CaptchaSiteRootSchema', title = _(u"ReCaptcha settings"),
                description = _(u"captcha_site_root_schema_main_description",
                                default = u"CAPTCHAs can protect the site from spam attacks by robots. "
                                          u"You'll need to register with ReCaptcha and  "
                                          u"add the API keys here to activate this service."))


class CaptchaSiteRootSchema(colander.MappingSchema):
    captcha_registration = colander.SchemaNode(
        colander.Boolean(),
        title = _(u"captcha_registration_title",
                  default = u"Require when registering on the site."),)
    captcha_meeting = colander.SchemaNode(
        colander.Boolean(),
        title = _(u"captcha_meeting_title",
                  default = u"Require when creating a new meeting. (If users are allowed to do that)"),)
    captcha_public_key = colander.SchemaNode(colander.String(),
                                             title = _(u"Public ReCaptcha key"),
                                             validator=html_string_validator,
                                             missing=u"")
    captcha_private_key = colander.SchemaNode(colander.String(),
                                              title = _(u"Private ReCaptcha key"),
                                              validator=html_string_validator,
                                              missing=u"")
