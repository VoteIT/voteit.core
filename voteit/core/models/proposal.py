import colander
from zope.interface import implements

from voteit.core.models.base_content import BaseContent
from voteit.core.security import ADD_PROPOSAL
from voteit.core import register_content_info
from voteit.core.models.interfaces import IProposal


class Proposal(BaseContent):
    """ Proposal content. """
    implements(IProposal)
    content_type = 'Proposal'
    omit_fields_on_edit = ('name',)
    allowed_contexts = ('AgendaItem',)
    add_permission = ADD_PROPOSAL
    

class ProposalSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String())


def includeme(config):
    register_content_info(ProposalSchema, Proposal, registry=config.registry)
