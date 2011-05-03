import colander

from voteit.core.models.base_content import BaseContent


class Poll(BaseContent):
    """ Poll content. """
    
    content_type = 'Poll'
    omit_fields_on_edit = ['name']
    allowed_contexts = ['AgendaItem']
    

class PollSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
