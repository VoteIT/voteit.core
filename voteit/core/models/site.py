import colander

from voteit.core.models.base_content import BaseContent
from voteit.core.models.users import Users

class SiteRoot(BaseContent):
    """ The root of the site. Contains all other objects. """
    
    content_type = 'SiteRoot'

    omit_fields_on_edit = ['name']
    allowed_contexts = []
    
    @property
    def users(self):
        return self['users']


class SiteRootSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
