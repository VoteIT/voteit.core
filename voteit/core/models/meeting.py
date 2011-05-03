import colander

from voteit.core.models.base_content import BaseContent


class Meeting(BaseContent):
    """ Meeting content. """
    content_type = 'Meeting'

    omit_fields_on_edit = ['name']
    allowed_contexts = ['SiteRoot']
    

class MeetingSchema(colander.MappingSchema):
    name = colander.SchemaNode(colander.String())
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
