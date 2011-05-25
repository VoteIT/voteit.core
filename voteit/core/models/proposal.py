import colander
import deform
from zope.interface import implements
from pyramid.security import Allow, DENY_ALL, ALL_PERMISSIONS

from voteit.core import VoteITMF as _
from voteit.core import security
from voteit.core import register_content_info
from voteit.core.models.base_content import BaseContent
from voteit.core.models.interfaces import IProposal


ACL = {}
ACL['locked'] = [(Allow, security.ROLE_ADMIN, ALL_PERMISSIONS),
                 (Allow, security.ROLE_MODERATOR, (security.VIEW,)),
                 (Allow, security.ROLE_PARTICIPANT, (security.VIEW,)),
                 (Allow, security.ROLE_VIEWER, (security.VIEW,)),
                 DENY_ALL,
                ]

LOCKED_STATES = ('retracted', 'voting', 'approved', 'denied', 'finished')


class Proposal(BaseContent):
    """ Proposal content. """
    implements(IProposal)
    content_type = 'Proposal'
    display_name = _(u"Proposal")
    allowed_contexts = ('AgendaItem',)
    add_permission = security.ADD_PROPOSAL

    @property
    def __acl__(self):
        state = self.get_workflow_state
        if state in LOCKED_STATES:
            return ACL['locked']
        raise AttributeError('Check parents ACL')


def construct_schema(**kwargs):
    class ProposalSchema(colander.MappingSchema):
        title = colander.SchemaNode(colander.String(),
                                    title = _(u"Proposal"),)
    return ProposalSchema()


def includeme(config):
    register_content_info(construct_schema, Proposal, registry=config.registry)
