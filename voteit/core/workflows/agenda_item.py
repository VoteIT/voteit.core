# -*- coding: utf-8 -*-
from arche.models.workflow import Workflow
from voteit.core import security

from voteit.core import _


class AgendaItemWorkflow(Workflow):
    """ The basic transitions for an Agenda item. """
    name = 'agenda_item_wf'
    title = _("Agenda item workflow")
    states = {'private': _("Private"),
              'upcoming': _("Upcoming"),
              'ongoing': _("Ongoing"),
              'closed': _("Closed")}
    transitions = {}
    initial_state = 'private'

    @classmethod
    def init_acl(cls, registry):
        _PRIV_MOD_PERMS = (security.VIEW,
                           security.EDIT,
                           security.DELETE,
                           security.MODERATE_MEETING,
                           security.CHANGE_WORKFLOW_STATE,)
        _CLOSED_AI_MOD_PERMS = (security.VIEW,
                                security.CHANGE_WORKFLOW_STATE,
                                security.ADD_DISCUSSION_POST,
                                security.MODERATE_MEETING,)
        aclreg = registry.acl
        private = aclreg.new_acl('AgendaItem:private')
        private.add(security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS)
        private.add(security.ROLE_ADMIN, _PRIV_MOD_PERMS)
        private.add(security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS)
        private.add(security.ROLE_MODERATOR, _PRIV_MOD_PERMS)
        closed_ai = aclreg.new_acl('AgendaItem:closed_ai')
        closed_ai.add(security.ROLE_ADMIN, _CLOSED_AI_MOD_PERMS)
        closed_ai.add(security.ROLE_MODERATOR, _CLOSED_AI_MOD_PERMS)
        closed_ai.add(security.ROLE_DISCUSS, security.ADD_DISCUSSION_POST)
        closed_ai.add(security.ROLE_VIEWER, security.VIEW)
        closed_meeting = aclreg.new_acl('AgendaItem:closed_meeting')
        closed_meeting.add(security.ROLE_ADMIN, security.VIEW)
        closed_meeting.add(security.ROLE_MODERATOR, security.VIEW)
        closed_meeting.add(security.ROLE_VIEWER, security.VIEW)


AgendaItemWorkflow.add_transitions(
    from_states='*',
    to_states='ongoing',
    title = _("Make ongoing"),
    permission=security.CHANGE_WORKFLOW_STATE
)


AgendaItemWorkflow.add_transitions(
    from_states='*',
    to_states='closed',
    title = _("Close"),
    permission=security.CHANGE_WORKFLOW_STATE

)


AgendaItemWorkflow.add_transitions(
    from_states='*',
    to_states='upcoming',
    title = _("Set as upcoming"),
    permission=security.CHANGE_WORKFLOW_STATE
)


AgendaItemWorkflow.add_transitions(
    from_states='*',
    to_states='private',
    title = _("Make private"),
    permission=security.CHANGE_WORKFLOW_STATE
)


def includeme(config):
    config.add_workflow(AgendaItemWorkflow)
    config.set_content_workflow('AgendaItem', 'agenda_item_wf')
