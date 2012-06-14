from betahaus.pyracont.decorators import schema_factory
import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator
from voteit.core.validators import richtext_validator


@schema_factory('AddAgendaItemSchema', title = _(u"Add agenda item"), description = _(u"Use this form to add an agenda item"))
@schema_factory('EditAgendaItemSchema', title = _(u"Edit agenda item"), description = _(u"Use this form to edit an agenda item"))
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
                        default=u"Place the the agenda item background information here. You can link to external documents and memos. It's also a good idea to add an image, it will make it easier for participants to quickly see which page they're on."),
        missing = u"",
        widget=deform.widget.RichTextWidget(),
        validator=richtext_validator,
    )
