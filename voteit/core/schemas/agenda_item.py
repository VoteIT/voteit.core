import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator
from voteit.core.validators import richtext_validator


class AgendaItemSchema(colander.MappingSchema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title"),
        description = _("Try keeping it under 20 characters."),
        validator=html_string_validator,)
    description = colander.SchemaNode(
        colander.String(),
        title = _("Description (In search results and similar)"),
        description = _("Not visible on the agenda page."),
        missing = "")
    body = colander.SchemaNode(
        colander.String(),
        title = _("Body"),
        description = _("agenda_item_schema_body",
                        default="Place the the agenda item background information here. "
                            "You can link to external documents and memos. It's also a good "
                            "idea to add an image, it will make it easier for participants "
                            "to quickly see which page they're on."),
        missing = "",
        widget=deform.widget.RichTextWidget(options = (('theme', 'advanced'),)),
        validator=richtext_validator,)


def includeme(config):
    config.add_content_schema('AgendaItem', AgendaItemSchema, ('add', 'edit'))
