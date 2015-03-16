from betahaus.viewcomponent import view_action
from pyramid.renderers import render
from pyramid.traversal import find_interface
from pyramid.traversal import find_root

from voteit.core.models.interfaces import IInviteTicket
from voteit.core.models.interfaces import IMeeting
from voteit.core.security import MEETING_ROLES


@view_action('email', 'invite_ticket', interface = IInviteTicket)
def invite_ticket(context, request, va, **kw):
    """ Render invite ticket email html.
        Uses ticket as a context.
        Requires message to be passed as a keyword when using view_action
    """
    #FIXME: Include meeting logo in mail?
    roles = dict(MEETING_ROLES)
    meeting = find_interface(context, IMeeting)
    root = find_root(meeting)
    assert meeting
    response = {}
    response['access_link'] = request.resource_url(meeting, 'ticket',
                                                   query = {'email': context.email, 'token': context.token})
    response['message'] = kw['message']
    response['meeting'] = meeting
    response['contact_mail'] = meeting.get_field_value('meeting_mail_address')
    response['sender_profile'] = root.users.get(context.sent_by)
    response['roles'] = [roles.get(x) for x in context.roles]
    return render('templates/email/invite_ticket_email.pt', response, request = request)
