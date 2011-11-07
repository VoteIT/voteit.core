import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator


@schema_factory('SiteRootSchema')
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
