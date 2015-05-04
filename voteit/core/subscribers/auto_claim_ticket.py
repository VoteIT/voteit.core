from arche.interfaces import IEmailValidatedEvent
from pyramid.threadlocal import get_current_request
from pyramid.traversal import find_resource
from pyramid.traversal import find_root

from voteit.core.models.invite_ticket import claim_ticket

def auto_claim_ticket(event):
    """ When an email address is validated check for existing
        tickets for this address and claim them.
    """
    root = find_root(event.user)
    address_for_docid = root.document_map.address_for_docid
    query = "type_name == 'Meeting' and "
    query += "workflow_state in any(['ongoing', 'upcoming'])"
    request = get_current_request()
    for docid in root.catalog.query(query)[1]:
        path = address_for_docid(docid)
        meeting = find_resource(root, path)
        if event.user.email in meeting.invite_tickets:
            ticket = meeting.invite_tickets[event.user.email]
            if ticket.get_workflow_state() == 'open':
                claim_ticket(ticket, request, event.user.userid)

def includeme(config):
    config.add_subscriber(auto_claim_ticket, IEmailValidatedEvent)
