import colander
from voteit.core.models.base_content import BaseContent
from voteit.core.security import ADD_PROPOSAL


class Proposal(BaseContent):
    """ Proposal content. """
    
    content_type = 'Proposal'
    omit_fields_on_edit = ('name',)
    allowed_contexts = ('AgendaItem',)
    add_permission = ADD_PROPOSAL
    

class ProposalSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())
