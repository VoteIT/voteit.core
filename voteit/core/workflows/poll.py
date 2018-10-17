# -*- coding: utf-8 -*-
from arche.models.workflow import Workflow

from voteit.core import _
from voteit.core import security


class PollWorkflow(Workflow):
    """ Poll workflow. """
    name = 'poll_wf'
    title = "Poll workflow"
    states = {'private': _("Private"),
              'upcoming': _("Upcoming"),
              'ongoing': _("Ongoing"),
              'closed': _("Closed"),
              'canceled': _("Canceled")}
    transitions = {}
    initial_state = 'private'

    @classmethod
    def init_acl(cls, registry):
        aclreg = registry.acl
        _UPCOMING_PERMS = (security.VIEW,
                           security.EDIT,
                           security.DELETE,
                           security.CHANGE_WORKFLOW_STATE,
                           security.MODERATE_MEETING,)
        _ONGOING_PERMS = (security.VIEW,
                          security.DELETE,
                          security.CHANGE_WORKFLOW_STATE,
                          security.MODERATE_MEETING,)

        private = aclreg.new_acl('%s:private' % cls.name)
        private.add(security.ROLE_ADMIN, _UPCOMING_PERMS)
        private.add(security.ROLE_MODERATOR, _UPCOMING_PERMS)
        upcoming = aclreg.new_acl('%s:upcoming' % cls.name)
        upcoming.add(security.ROLE_ADMIN, _UPCOMING_PERMS)
        upcoming.add(security.ROLE_MODERATOR, _UPCOMING_PERMS)
        upcoming.add(security.ROLE_VIEWER, security.VIEW)
        ongoing = aclreg.new_acl('%s:ongoing' % cls.name)
        ongoing.add(security.ROLE_ADMIN, _ONGOING_PERMS)
        ongoing.add(security.ROLE_MODERATOR, _ONGOING_PERMS)
        ongoing.add(security.ROLE_VOTER, security.ADD_VOTE)
        ongoing.add(security.ROLE_VIEWER, security.VIEW)
        closed = aclreg.new_acl('%s:closed' % cls.name)
        closed.add(security.ROLE_ADMIN, [security.VIEW, security.DELETE, security.MODERATE_MEETING])
        closed.add(security.ROLE_MODERATOR,
                   [security.VIEW, security.DELETE, security.MODERATE_MEETING])
        closed.add(security.ROLE_VIEWER, security.VIEW)
        canceled = aclreg.new_acl('%s:canceled' % cls.name)
        canceled.add(security.ROLE_ADMIN, _ONGOING_PERMS)
        canceled.add(security.ROLE_MODERATOR, _ONGOING_PERMS)
        canceled.add(security.ROLE_VIEWER, security.VIEW)


PollWorkflow.add_transitions(
    from_states='private',
    to_states='upcoming',
    title=_("Set upcoming"),
    permission=security.CHANGE_WORKFLOW_STATE
)


PollWorkflow.add_transitions(
    from_states='upcoming',
    to_states='private',
    title=_("Make private again"),
    permission=security.CHANGE_WORKFLOW_STATE

)


PollWorkflow.add_transitions(
    from_states='upcoming',
    to_states='ongoing',
    title=_("Start poll"),
    permission=security.CHANGE_WORKFLOW_STATE
)


PollWorkflow.add_transitions(
    from_states='ongoing',
    to_states='canceled',
    title=_("Cancel poll"),
    permission=security.CHANGE_WORKFLOW_STATE
)


PollWorkflow.add_transitions(
    from_states=('canceled', 'ongoing'),
    to_states='closed',
    title=_("Close poll"),
    permission=security.CHANGE_WORKFLOW_STATE
)


def includeme(config):
    config.add_workflow(PollWorkflow)
    config.set_content_workflow('Poll', 'poll_wf')
