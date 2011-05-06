import colander
from pyramid.security import Allow, DENY_ALL

from voteit.core.models.base_content import BaseContent
from voteit.core.security import EDIT, ROLE_OWNER

class Proposal(BaseContent):
    """ Proposal content. """
    
    content_type = 'Proposal'
    omit_fields_on_edit = ['name']
    allowed_contexts = ['AgendaItem']
    
    __acl__ = [(Allow, ROLE_OWNER, EDIT),
               DENY_ALL]
    

class ProposalSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
