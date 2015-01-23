import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator
from voteit.core.validators import richtext_validator


# @schema_factory('AddAgendaItemSchema', title = _(u"Add agenda item"),
#                 provides = IAgendaItemSchema)
# @schema_factory('EditAgendaItemSchema', title = _(u"Edit agenda item"),
#                 provides = IAgendaItemSchema)
class AgendaItemSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(),
        title = _(u"Title"),
        description = _(u"Avoid a title with more than 20 characters"),
        validator=html_string_validator,
    )
    description = colander.SchemaNode(
        colander.String(),
        title = _(u"Description"),
        description = _(u"agenda_item_description_description",
                        default=u"Place the the agenda item background information here. "
                            u"You can link to external documents and memos. It's also a good "
                            u"idea to add an image, it will make it easier for participants "
                            u"to quickly see which page they're on."),
        missing = u"",
        widget=deform.widget.RichTextWidget(options = (('theme', 'advanced'),)),
        validator=richtext_validator,
    )



def includeme(config):
    config.add_content_schema('AgendaItem', AgendaItemSchema, 'add')
    config.add_content_schema('AgendaItem', AgendaItemSchema, 'edit')
