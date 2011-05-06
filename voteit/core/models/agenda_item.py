import colander

from voteit.core.models.base_content import BaseContent
from voteit.core.security import ADD_AGENDA_ITEM


class AgendaItem(BaseContent):
    """ Agenda Item content. """
    content_type = 'AgendaItem'
    omit_fields_on_edit = ('name',)
    allowed_contexts = ('Meeting',)
    add_permission = ADD_AGENDA_ITEM
    

class AgendaItemSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
