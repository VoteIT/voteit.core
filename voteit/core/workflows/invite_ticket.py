# -*- coding: utf-8 -*-
from arche.models.workflow import Workflow

from voteit.core import _
#from voteit.core import security


class InviteTicketWorkflow(Workflow):
    """ Invite tickets can only be open or closed. Open tickets aren't used. """
    name = 'invite_ticket_wf'
    title = _("Invite ticket workflow")
    states = {'open': _("Open"),
              'closed': _("Closed")}
    transitions = {}
    initial_state = 'open'

    @classmethod
    def init_acl(cls, registry):
        pass


InviteTicketWorkflow.add_transitions(
    from_states='open',
    to_states='closed',
    title = _("Closed"),
)


InviteTicketWorkflow.add_transitions(
    from_states='closed',
    to_states='open',
    title = _("Open"),
)


def includeme(config):
    config.add_workflow(InviteTicketWorkflow)
    config.set_content_workflow('InviteTicket', 'invite_ticket_wf')
