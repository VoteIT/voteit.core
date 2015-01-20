from __future__ import unicode_literals

from betahaus.pyracont.decorators import schema_factory
import colander
import deform

from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator
from voteit.core.schemas.agenda_item import AgendaItemSchema


class AgendaItemSequenceSchema(colander.SequenceSchema):
    agenda_item = AgendaItemSchema(title=_(u'Agenda item'))


# @schema_factory('AgendaTemplateSchema',
#                 title = _(u"Agenda template"))
class AgendaTemplateSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Template name"),
        validator=html_string_validator,)
    description = colander.SchemaNode(
        colander.String(),
        title = _("Description"),
        description = _("agenda_template_description_description",
                        default="Describe the purpose of this agenda"),
        widget=deform.widget.TextAreaWidget(rows=5, cols=40),
    )
    agenda_items = AgendaItemSequenceSchema(title=_('Agenda items'))


def includeme(config):
    config.add_content_schema('AgendaTemplate', AgendaTemplateSchema, 'edit')
    config.add_content_schema('AgendaTemplate', AgendaTemplateSchema, 'add')
