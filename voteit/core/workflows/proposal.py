# -*- coding: utf-8 -*-
from arche.models.workflow import Workflow

from voteit.core import _
from voteit.core import security


class ProposalWorkflow(Workflow):
    """ Handles states and permissions for proposals. """
    name = 'proposal_wf'
    title = "Proposal workflow"
    states = {'published': _("Published"),
              'retracted': _("Retracted"),
              'voting': _("Locked for voting"),
              'approved': _("Approved"),
              'denied': _("Denied"),
              'unhandled': _("Unhandled")}
    transitions = {}
    initial_state = 'published'

    @classmethod
    def init_acl(cls, registry):
        _PUBLISHED_MODERATOR_PERMS = (security.VIEW,
                                      security.EDIT,
                                      security.DELETE,
                                      security.RETRACT,
                                      security.MODERATE_MEETING,)
        _LOCKED_MODERATOR_PERMS = (security.VIEW,
                                   security.EDIT,
                                   security.DELETE,
                                   security.MODERATE_MEETING,)
        aclreg = registry.acl
        # Default state if wf doesn't have state settings
        default_acl = aclreg.new_acl('Proposal')
        default_acl.add(security.ROLE_ADMIN, _LOCKED_MODERATOR_PERMS)
        default_acl.add(security.ROLE_MODERATOR, _LOCKED_MODERATOR_PERMS)
        default_acl.add(security.ROLE_VIEWER, security.VIEW)
        # The permissive 'published' state within the wf
        published = aclreg.new_acl('%s:published' % cls.name)
        published.add(security.ROLE_ADMIN, _PUBLISHED_MODERATOR_PERMS)
        published.add(security.ROLE_MODERATOR, _PUBLISHED_MODERATOR_PERMS)
        published.add(security.ROLE_OWNER, security.RETRACT)
        published.add(security.ROLE_VIEWER, security.VIEW)
        published.add(security.ROLE_VOTER, security.ADD_SUPPORT)
        # The below part is a state that's activated depending on the Agenda Item.
        # It will override the wf for the proposals state
        closed = aclreg.new_acl('Proposal:closed')
        closed.add(security.ROLE_ADMIN, security.VIEW)
        closed.add(security.ROLE_MODERATOR, security.VIEW)
        closed.add(security.ROLE_VIEWER, security.VIEW)
        private = aclreg.new_acl('Proposal:private', description="When Agenda Item is private")
        private.add(security.ROLE_ADMIN, _PUBLISHED_MODERATOR_PERMS)
        private.add(security.ROLE_MODERATOR, _PUBLISHED_MODERATOR_PERMS)


ProposalWorkflow.add_transitions(
    from_states='published',
    to_states='retracted',
    title = _("Retract"),
    permission=security.RETRACT
)


ProposalWorkflow.add_transitions(
    from_states='published',
    to_states='voting',
    title = _("Lock for voting"),
    permission=security.MODERATE_MEETING
)


ProposalWorkflow.add_transitions(
    from_states=('published', 'voting', 'denied'),
    to_states='approved',
    title = _("Approved"),
    permission=security.MODERATE_MEETING
)


ProposalWorkflow.add_transitions(
    from_states=('published', 'voting', 'approved'),
    to_states='denied',
    title = _("Denied"),
    permission=security.MODERATE_MEETING
)


ProposalWorkflow.add_transitions(
    from_states='published',
    to_states='unhandled',
    title = _("Unhandled"),
    permission=security.MODERATE_MEETING
)


ProposalWorkflow.add_transitions(
    from_states='*',
    to_states='published',
    title = _("Back to published"),
    permission=security.MODERATE_MEETING
)


def includeme(config):
    config.add_workflow(ProposalWorkflow)
    config.set_content_workflow('Proposal', 'proposal_wf')
