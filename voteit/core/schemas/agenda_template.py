from betahaus.pyracont.decorators import schema_factory
import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator
from voteit.core.schemas.agenda_item import AgendaItemSchema


class AgendaItemSequenceSchema(colander.SequenceSchema):
    agenda_item = AgendaItemSchema(title=_(u'Agenda item'))


@schema_factory('AgendaTemplateSchema',
                title = _(u"Agenda template"))
class AgendaTemplatesSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_(u"Template name"),
        validator=html_string_validator,)
    description = colander.SchemaNode(
        colander.String(),
        title = _(u"Description"),
        description = _(u"agenda_template_description_description",
                        default=u"Describe the purpose of this agenda"),
        widget=deform.widget.TextAreaWidget(rows=5, cols=40),
    )
    
    agenda_items = AgendaItemSequenceSchema(title=_(u'Agenda items'))