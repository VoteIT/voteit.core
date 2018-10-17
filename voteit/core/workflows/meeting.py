# -*- coding: utf-8 -*-
from arche.models.workflow import Workflow

from voteit.core import _
from voteit.core import security


class MeetingWorkflow(Workflow):
    """ The basic transitions for a meeting. """
    name = 'meeting_wf'
    title = _("Meeting workflow")
    states = {'upcoming': _("Upcoming"),
              'ongoing': _("Ongoing"),
              'closed': _("Closed")}
    transitions = {}
    initial_state = 'upcoming'

    @classmethod
    def init_acl(cls, registry):
        _MODERATOR_DEFAULTS = (security.VIEW,
                               security.EDIT,
                               security.MANAGE_GROUPS,
                               security.MODERATE_MEETING,
                               security.DELETE,
                               security.CHANGE_WORKFLOW_STATE,
                               security.ADD_INVITE_TICKET)
        aclreg = registry.acl
        default_acl = aclreg.new_acl('Meeting')
        default_acl.add(security.ROLE_ADMIN, security.REGULAR_ADD_PERMISSIONS)
        default_acl.add(security.ROLE_ADMIN, security.MANAGE_SERVER)
        default_acl.add(security.ROLE_ADMIN, _MODERATOR_DEFAULTS)
        default_acl.add(security.ROLE_MODERATOR, security.REGULAR_ADD_PERMISSIONS)
        default_acl.add(security.ROLE_MODERATOR, _MODERATOR_DEFAULTS)
        default_acl.add(security.ROLE_DISCUSS, security.ADD_DISCUSSION_POST)
        default_acl.add(security.ROLE_PROPOSE, security.ADD_PROPOSAL)
        default_acl.add(security.ROLE_VIEWER, security.VIEW)
        closed_acl = aclreg.new_acl('meeting_wf:closed')
        closed_acl.add(security.ROLE_ADMIN, (security.VIEW,
                                             security.MODERATE_MEETING,
                                             security.MANAGE_GROUPS,
                                             security.DELETE,
                                             security.CHANGE_WORKFLOW_STATE))
        closed_acl.add(security.ROLE_MODERATOR, (security.VIEW,
                                                 security.MODERATE_MEETING,
                                                 security.MANAGE_GROUPS,))
        closed_acl.add(security.ROLE_VIEWER, security.VIEW)


MeetingWorkflow.add_transitions(
    from_states='*',
    to_states='ongoing',
    title = _("Start meeting"),
    permission=security.CHANGE_WORKFLOW_STATE
)


MeetingWorkflow.add_transitions(
    from_states='*',
    to_states='closed',
    title = _("Close meeting"),
    permission=security.CHANGE_WORKFLOW_STATE

)


MeetingWorkflow.add_transitions(
    from_states='*',
    to_states='upcoming',
    title = _("Set as upcoming"),
    permission=security.CHANGE_WORKFLOW_STATE
)


def includeme(config):
    config.add_workflow(MeetingWorkflow)
    config.set_content_workflow('Meeting', 'meeting_wf')
