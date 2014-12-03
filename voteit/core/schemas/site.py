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
                                      widget=deform.widget.RichTextWidget(options = (('theme', 'advanced'),)),
                                      validator=richtext_validator,)
    site_title = colander.SchemaNode(colander.String(),
                                title = _(u"Site title"),
                                description = _(u"Displayed in the header when you're not in a meeting. Keep it short!"),
                                validator=html_string_validator,)
    footer = colander.SchemaNode(colander.String(),
                                      title = _(u"Footer"),
                                      missing = u"",
                                      widget=deform.widget.RichTextWidget(options = (('theme', 'advanced'),)),
                                      validator=richtext_validator,)
    registration_info = colander.SchemaNode(colander.String(),
                                      title = _(u"Registration info"),
                                      description = _(u"site_root_registration_info_description",
                                                      default = u"Information displayed on the registration page, right hand side."),
                                      missing = u"",
                                      widget=deform.widget.RichTextWidget(options = (('theme', 'advanced'),)),
                                      validator=richtext_validator,)
    allow_add_meeting = colander.SchemaNode(colander.Boolean(),
                                            title = _(u"Allow authenticated users to add meetings"),
                                            default = False,)
    support_email = colander.SchemaNode(colander.String(),
           title = _(u"Support email for this site"),
           description = _(u"support_email_schema_desription",
                           default = u"This email will receive mail sent through the support request form visible in the help menu."),
           validator = colander.Email(),) 


@schema_factory('LayoutSiteRootSchema', title = _(u"Layout"),
                description = _(u"layout_site_root_schema_description",
                                default = u"Global layout settings"))
class LayoutSiteRootSchema(colander.Schema):
    default_logo_url = colander.SchemaNode(colander.String(),
                                           title = _(u"URL to a default logo used in meetings and in the site root."),
                                           description = _(u"logo_description_text",
                                                           default = u"It will be shown to the left of the header. "
                                                           u"Dimensions should be no more than the text height. "
                                                           u"If you use the wrong dimensions, you may break the layout."),
                                           missing = u"")
    custom_css = colander.SchemaNode(colander.String(),
                                     title = _(u"Custom CSS code to inject in each page."),
                                     description = _(u"custom_css_code_descrption",
                                                     default = u"Use this for small customisation. "
                                                               u"Note that you may break the site horribly if you tinker with this!"),
                                     missing = u"",
                                     widget = deform.widget.TextAreaWidget(cols = 80, rows = 20))
